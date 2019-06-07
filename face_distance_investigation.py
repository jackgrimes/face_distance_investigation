import os
import face_recognition
import matplotlib.pyplot as plt
import numpy as np
from sklearn import metrics
import datetime
from scipy.stats import norm
import pandas as pd

doing_graphs = True
doing_precision_recall = True

#
##INITIALISATIONS
#

overall_start_time = datetime.datetime.now()

# Provide path to faces dataset

base_directory = r'C:\dev\data\lfw'

# Define allowed extensions for the images to scan

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def timesince(time, percent_done):
    """Returns a string of the time taken so far, and an estimate of the time remaining (given the time taken so far and the percentage complete"""
    diff = datetime.datetime.now() - time
    days, seconds = diff.days, diff.seconds
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    try:
        remaining_diff = (diff / percent_done) * 100 - diff
        remaining_days, remaining_seconds = remaining_diff.days, remaining_diff.seconds
        remaining_hours = remaining_days * 24 + remaining_seconds // 3600
        remaining_minutes = (remaining_seconds % 3600) // 60
        remaining_seconds = remaining_seconds % 60
        return (str(hours) + " hours, " + str(minutes) + " minutes, " + str(seconds) + " seconds taken so far" + "\n" +
                "Estimated " + str(remaining_hours) + " hours, " + str(remaining_minutes) + " minutes, " + str(
                    remaining_seconds) + " seconds to completion")
    except:
        return ("Cannot calculate times done and remaining at this time")


def time_diff(time1, time2):
    """Returns a sting of duration between two times"""
    diff = time2 - time1
    days, seconds = diff.days, diff.seconds
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return str(hours) + " hours, " + str(minutes) + " minutes, " + str(seconds) + " seconds taken"


def allowed_file(filename):
    """A check if the file in question has an allowed extension type"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def encodings_builder(base_directory, image_no_max, image_attempt_no_max, attempting_all, encodings_start_time,
                      start_time):
    all_encodings = []
    person_no = 0
    image_no = 1
    image_attempt_no = 1
    failed_attempts = 0
    images_without_faces = []
    for person in os.listdir(base_directory):
        person_path = os.path.join(base_directory, person)
        person_no += 1
        if person != "Thumbs.db":
            this_persons_successful_encodings = 0
            for image in os.listdir(person_path):
                image_path = os.path.join(person_path, image)
                if image != "Thumbs.db" and allowed_file(image):
                    loaded_image = face_recognition.load_image_file(image_path)
                    if attempting_all:
                        print(
                            "Now scanning " + person + ", image " + str(image_attempt_no) + " of " + str(image_no_max) +
                            " (" + str(round(100 * (image_attempt_no - 1) / image_no_max, 2)) + "% completed)." +
                            " (" + str(failed_attempts) + " images have failed.)\n" +
                            timesince(start_time, 100 * (image_attempt_no - 1) / image_no_max) + " of scans")
                    else:
                        print("Now scanning " + person + ", image " + str(image_no) + " of " + str(image_no_max) +
                              " (" + str(round(100 * (image_no - 1) / image_no_max, 2)) + "% completed). " +
                              timesince(start_time, 100 * (image_no - 1) / image_no_max) + " of scans")
                    encodings = face_recognition.face_encodings(loaded_image)
                    if len(encodings) > 0:
                        all_encodings.append([person_path, image_path, encodings])
                        if (image_no >= image_no_max) or (image_attempt_no >= image_attempt_no_max):
                            return all_encodings, image_no, person_no, image_attempt_no, failed_attempts, images_without_faces
                        image_no += 1
                        image_attempt_no += 1
                        this_persons_successful_encodings += 1
                        print("")
                    else:
                        print("No face found this image")
                        print("")
                        image_attempt_no += 1
                        failed_attempts += 1
                        images_without_faces.append(image_path)
            if this_persons_successful_encodings == 0:
                person_no -= 1
    return all_encodings, image_no, person_no, image_attempt_no, failed_attempts, images_without_faces


def run():
    # Allow user to compare only a subset of the faces

    print("")
    image_no_max = input("How many images do you want to compare? (leave blank for all)")

    # Count the number of folders (people) in dataset, if no number defined then compare with all

    person_count = len(([len(files) for r, d, files in os.walk(base_directory)])) - 1

    # Count images

    if image_no_max == "":
        attempting_all = True
    else:
        image_no_max = int(image_no_max)
        attempting_all = False

    if attempting_all:
        print("")
        print("Counting the images...\n")
        file_count = 0
        person_no = 0
        for _, dirs, files in os.walk(base_directory):
            person_no += 1
            file_count += len([x for x in files if x != "Thumbs.db"])
        image_no_max = file_count

    print(str(image_no_max) + " files to attempt to scan and compare")
    print("")

    #
    ##BUILD UP THE ENCODINGS DATASET
    #

    encodings_start_time = datetime.datetime.now()

    # Initialise counters for building up encodings list

    start_time = datetime.datetime.now()

    # Build up the encodings

    all_encodings, image_no, person_no, image_attempt_no, failed_attempts, images_without_faces = encodings_builder(
        base_directory, image_no_max, image_no_max, attempting_all, encodings_start_time, start_time)

    #
    ##COMPARE THE ENCODINGS
    #

    comparisons_start_time = datetime.datetime.now()

    print("\n" + comparisons_start_time.strftime("%Y_%m_%d %H:%M:%S") + " Doing the comparisons..." + "\n")

    # Initialisations

    all_comparisons = []
    image_counter = 1
    same_face_distances = []
    different_face_distances = []
    comparison_counter = 0
    total_comparisons = (len(all_encodings) * (len(all_encodings) - 1)) / 2
    start_time = datetime.datetime.now()

    # Looping over combinations of images, and getting face_distance for each pair

    for image in range(1, len(all_encodings)):
        for image2 in range(0, image):
            distances = []
            for face1 in range(len(all_encodings[image][2])):
                for face2 in range(len(all_encodings[image2][2])):
                    distances.append(face_recognition.face_distance([all_encodings[image][2][face1]],
                                                                    all_encodings[image2][2][face2])[0])
            if len(distances) > 0:
                comparison_counter += 1
                if comparison_counter % 1000000 == 0:
                    print(
                        "Comparison number " + str(comparison_counter) + " of " + str(round(total_comparisons)) + " (" +
                        str(round(100 * comparison_counter / total_comparisons, 2)) + "% completed). " +
                        timesince(start_time, 100 * (comparison_counter / total_comparisons)) + " of comparisons")
                    print("")
                distance = min(distances)
                same = all_encodings[image][0] == all_encodings[image2][0]
                if same:
                    same_face_distances.append((all_encodings[image][1], all_encodings[image2][1], distance))
                else:
                    different_face_distances.append((all_encodings[image][1], all_encodings[image2][1], distance))
        image_counter += 1

    same_face_distances_df = pd.DataFrame(same_face_distances, columns=['path1', 'path2', 'distance'])
    different_face_distances_df = pd.DataFrame(different_face_distances, columns=['path1', 'path2', 'distance'])

    same_face_distances = list(same_face_distances_df['distance'])
    different_face_distances = list(different_face_distances_df['distance'])

    print(datetime.datetime.now().strftime("%Y_%m_%d %H:%M:%S") + " Image comparisons completed!")
    print("")

    #
    ##GRAPHS
    #

    graph_start_time = datetime.datetime.now()

    if attempting_all:
        file_str_prefix = os.path.join(r"C:\dev\data\face_distance_investigation",
                                       graph_start_time.strftime("%Y_%m_%d %H_%M_%S_") + "_attempting_all_images_")
    else:
        file_str_prefix = os.path.join(r"C:\dev\data\face_distance_investigation",
                                       graph_start_time.strftime("%Y_%m_%d %H_%M_%S_") + "_attempting_" + str(
                                           image_no_max) + "_images_")

    if doing_graphs:
        print(datetime.datetime.now().strftime("%Y_%m_%d %H:%M:%S") + " Now making the graphs...")
        print("")

        # Histogram without fitted distribution

        fig = plt.figure()
        fig.clf()
        xmin, xmax = min(min(same_face_distances), min(different_face_distances)), max(max(same_face_distances),
                                                                                       max(different_face_distances))
        bins = np.linspace(xmin, xmax, 100)
        ax = fig.add_subplot(111)
        plt.hist(same_face_distances, bins, alpha=0.5, label='same faces', density=True, edgecolor='black',
                 linewidth=1.2, color='green')
        plt.hist(different_face_distances, bins, alpha=0.5, label='different faces', density=True, edgecolor='black',
                 linewidth=1.2, color='blue')
        plt.legend(loc='upper right')
        plt.text(0.15, 0.9, str(comparison_counter) + " comparisons of \n" + str(image_no) + " images of \n " + str(
            person_no) + " people",
                 ha='center', va='center', transform=ax.transAxes)
        fig.set_size_inches(12, 8)
        plt.xlabel("Face distance")
        plt.ylabel("Probability density")
        fig.savefig(file_str_prefix + r'_1_distributions_same_diff_distances.png')

        # Histogram with fitted distribution

        mu_sf, std_sf = norm.fit(same_face_distances)
        mu_df, std_df = norm.fit(different_face_distances)
        points_for_lines = np.linspace(xmin, xmax, 10000)
        p_sf = norm.pdf(points_for_lines, mu_sf, std_sf)
        p_df = norm.pdf(points_for_lines, mu_df, std_df)

        plt.plot(points_for_lines, p_sf, 'k', linewidth=2)
        plt.plot(points_for_lines, p_df, 'k', linewidth=2)
        title = "Fit results: mu = {}, std = {}, mu = {}, std = {}".format(round(mu_sf, 2), round(std_sf, 2),
                                                                           round(mu_df, 2), round(std_df, 2))
        plt.title(title)
        fig.savefig(file_str_prefix + r'_2_distributions_same_diff_distances_with_norm.png')

        # Cumulative histogram without fitted distribution

        fig.clf()
        plt.hist(same_face_distances, bins, alpha=0.5, label='same faces', density=True, edgecolor='black',
                 linewidth=1.2, cumulative=1, color='green')
        plt.hist(different_face_distances, bins, alpha=0.5, label='different faces', density=True, edgecolor='black',
                 linewidth=1.2, cumulative=1, color='blue')
        plt.legend(loc='lower right')
        plt.text(0.15, 0.9, str(comparison_counter) + " comparisons of \n" + str(image_no) + " images of \n " + str(
            person_no) + " people",
                 ha='center', va='center', transform=ax.transAxes)
        fig.set_size_inches(12, 8)
        plt.xlabel("Face distance")
        plt.ylabel("Cumulative probability")
        fig.savefig(file_str_prefix + r'_3_distributions_same_diff_distances_cum.png')

        # Cumulative histogram with fitted distribution

        p_sf = norm.cdf(points_for_lines, mu_sf, std_sf)
        p_df = norm.cdf(points_for_lines, mu_df, std_df)
        plt.plot(points_for_lines, p_sf, 'k', linewidth=2)
        plt.plot(points_for_lines, p_df, 'k', linewidth=2)
        title = "Fit results: mu = {}, std = {}, mu = {}, std = {}".format(round(mu_sf, 2), round(std_sf, 2),
                                                                           round(mu_df, 2), round(std_df, 2))
        plt.title(title)
        fig.savefig(file_str_prefix + r'_4_distributions_same_diff_distances_with_norm_cum.png')

        # ROC and AUC

        scores = np.concatenate((same_face_distances, different_face_distances), axis=0)
        y = np.concatenate((np.array([1] * len(same_face_distances)), np.array([0] * len(different_face_distances))),
                           axis=0)
        fpr, tpr, thresholds = metrics.roc_curve(y, scores, pos_label=1)
        auc = metrics.auc(tpr, fpr)
        fig = plt.figure()
        fig.set_size_inches(12, 8)
        plt.plot(tpr, fpr)
        plt.xlabel("True positive rate")
        plt.ylabel("False positive rate")
        title = "ROC Curve (AUC = {})".format(round(auc, 4))
        plt.title(title)
        plt.text(0.9, 0.1, str(comparison_counter) + " comparisons of \n" + str(image_no) + " images of \n " + str(
            person_no) + " people",
                 ha='center', va='center', transform=ax.transAxes)
        fig.savefig(file_str_prefix + r'_5_ROC.png')

        print(datetime.datetime.now().strftime("%Y_%m_%d %H:%M:%S") + " Graphs completed.")
        print("")

    #
    ##PRECISION, RECALL
    #

    precision_recall_start_time = datetime.datetime.now()

    if doing_precision_recall == True:
        print(datetime.datetime.now().strftime("%Y_%m_%d %H:%M:%S") + " Now doing precision and recall calculations...")
        print("")

        bin_boundaries = [0, 0.1] + [round(x, 2) for x in np.arange(0.2, 1.1, 0.01)] + [1.2, 1.3, 1.4, 1.5, 2]

        same_faces_binned = pd.DataFrame({'same_faces': same_face_distances})
        same_faces_binned['same_faces_freq'] = pd.cut(same_faces_binned.same_faces, bin_boundaries)

        different_faces_binned = pd.DataFrame({'different_faces': different_face_distances})
        different_faces_binned['different_faces_freq'] = pd.cut(different_faces_binned.different_faces, bin_boundaries)

        precision_recall_table = pd.concat([same_faces_binned.same_faces_freq.value_counts(),
                                            different_faces_binned.different_faces_freq.value_counts()], axis=1,
                                           sort=True)

        precision_recall_table['same_faces_freq_cum'] = precision_recall_table['same_faces_freq'].cumsum() - \
                                                        precision_recall_table['same_faces_freq']

        precision_recall_table['different_faces_freq_cum'] = precision_recall_table['different_faces_freq'].cumsum() - \
                                                             precision_recall_table['different_faces_freq']
        precision_recall_table['different_faces_freq_anti_cum'] = sum(precision_recall_table['different_faces_freq']) - \
                                                                  precision_recall_table['different_faces_freq_cum']

        precision_recall_table['cutoff'] = [
            float(str(x).split('(')[1].split(',')[0].replace(' ', '').replace("'", "").replace(']', '')) for x in
            list(precision_recall_table.index)]

        precision_recall_table['precision'] = precision_recall_table['same_faces_freq_cum'] / (
                precision_recall_table['same_faces_freq_cum'] + precision_recall_table['different_faces_freq_cum'])
        precision_recall_table['recall'] = precision_recall_table['same_faces_freq_cum'] / (
            sum(precision_recall_table['same_faces_freq']))

        precision_recall_table.to_csv(file_str_prefix + '_6_precision_recall_table.csv')

        print(datetime.datetime.now().strftime("%Y_%m_%d %H:%M:%S") + " Precision and recall calculations completed.")

    #
    ##RUN OUTPUTS
    #

    completion_time = datetime.datetime.now()

    outputs_str = ""

    if attempting_all:
        outputs_str += (str(image_attempt_no) + " images attempted.\n")
        outputs_str += ("faces not found in " + str(failed_attempts) + " images.\n")
    outputs_str += (str(image_no) + " images succeeded.")
    if (len(images_without_faces) > 0):
        outputs_str += ("\n\nImages without faces:\n\n" +
                        "\n".join(images_without_faces) +
                        "\n\n")
    outputs_str += ("Summary of time taken:\n\n" +
                    time_diff(overall_start_time, encodings_start_time) + ' on initial prep, counting pictures etc\n' +
                    time_diff(encodings_start_time, comparisons_start_time) + ' on getting encodings\n' +
                    time_diff(comparisons_start_time, graph_start_time) + ' on comparing encodings\n' +
                    time_diff(graph_start_time, precision_recall_start_time) + ' on making graphs\n' +
                    time_diff(precision_recall_start_time,
                              completion_time) + ' on calculation precision_recall_table\n\n' +
                    time_diff(overall_start_time, completion_time) + ' in total')

    file = open(file_str_prefix + "_7_run_notes.txt", "w")
    file.write(outputs_str)
    file.close()

    print('\n' + outputs_str)

    print('\nAll Done!')

    # Most similar lookalikes

    different_face_distances_df_sorted = different_face_distances_df.sort_values(by=['distance'], ascending=True)
    different_face_distances_df_sorted.head(50).to_csv(file_str_prefix + '_different_faces_looking_similar.csv',
                                                       index=False)

    # Most different photos of the same person

    same_face_distances_df_sorted = same_face_distances_df.sort_values(by=['distance'], ascending=False)
    same_face_distances_df_sorted.head(50).to_csv(file_str_prefix + '_same_face_looking_different.csv', index=False)


if __name__ == "__main__":
    run()
