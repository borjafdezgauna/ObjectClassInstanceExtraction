import argparse
import os
import common
import common.ner_result
import common.performance_metrics
from datetime import date
import math
import tqdm

def PrintErrorStats(writer, errors):
    #errors.sort(key=lambda x: len(x.items), reverse=False)
    for labelError in errors:
        writer.write(f"{labelError['description']} ({labelError['num_items']})\n")


def PrintAveragedStats(writer, stats):
    meanP = 0
    meanR = 0
    meanF1 = 0
    stdevP = 0
    stdevR = 0
    stdevF1 = 0
    for stat in stats:
    
        meanP = meanP + stat.precision
        meanR = meanR + stat.recall
        meanF1 = meanF1 + stat.f1
    
    meanP /= len(stats)
    meanR /= len(stats)
    meanF1 /= len(stats)
    for stat in stats:
        stdevP = stdevP + (stat.precision - meanP) * (stat.precision - meanP)
        stdevR = stdevR + (stat.recall - meanR) * (stat.recall - meanR)
        stdevF1 = stdevF1 + (stat.f1 - meanF1) * (stat.f1 - meanF1)
    
    stdevP = math.sqrt(stdevP / len(stats))
    stdevR = math.sqrt(stdevR / len(stats))
    stdevF1 = math.sqrt(stdevF1 / len(stats))

    writer.write(f" Pr= {meanP} ({stdevP}), Re= {meanR} ({stdevR}), F1= {meanF1} ({stdevF1})\n")


def PrintStats(writer, stats):
        
    if len(stats.items) > 0:
        writer.write(
            f" Pr= {stats.precision}," +
            f" Re= {stats.recall}," +
            f" F1= {stats.f1}," +
            f" Num.Items = {len(stats.items)}," +
            f" Negative impact = {(1- stats.f1) * len(stats.items)}\n")
    else:
        writer.write("N/A")


def MeasurePerformance(expected_results_file, actual_results_file, item_id):
    if os.path.exists(expected_results_file) and os.path.exists(actual_results_file):
        print(f"Measuring performance: {expected_results_file} (expected) vs {actual_results_file} (actual)")
        expected_result = common.ner_result.NerResult.load(expected_results_file)
        actual_result = common.ner_result.NerResult.load(actual_results_file)
        stats = common.performance_metrics.PerformanceMetrics.calculate(expected_result, actual_result, item_id)
        return stats

    elif os.path.exists(expected_results_file):
        print(f"No results found for: {expected_results_file}")
    else:
        print("Unknown error matching results files")
    return None

def MeasurePerformanceFromFolder(expected_folder, actual_folder, num_folds, merged_stats_folder):
    all_folds_stats = []
    all_folds_per_expected_or_predicted_label_stats = {}
    all_folds_per_expected_label_stats = {}

    for fold in range(0, num_folds):
        fold_stats = []
        expected_results_folder = f"{expected_folder}-{fold}"
        actual_results_folder = f"{actual_folder}-{fold}"

        fold_folder = f"{actual_folder}-{fold}"
        fold_stats_folder = f"{fold_folder}/Stats"
        if not os.path.exists(fold_stats_folder):
            os.makedirs(fold_stats_folder)

        for dirpaths, dirnames, filenames in os.walk(expected_results_folder):
            for filename in filenames:
                if (filename.endswith('.test.xml')):
                    item_id = (int) (filename.split('.')[0])
                    expected_results_file = os.path.join(dirpaths,filename)
                    actual_results_file = os.path.join(actual_results_folder, filename.replace('.test.xml', '.result.xml'))
                    stats = MeasurePerformance(expected_results_file, actual_results_file, item_id)
                    if stats:
                        fold_stats.append(stats)
                    
        mergedStats = common.performance_metrics.PerformanceStats.merge(fold_stats)
        all_folds_stats.append(mergedStats)
        expectedAndPredictedLabels = common.performance_metrics.PerformanceStats.labels(mergedStats, True)
        expectedLabels = common.performance_metrics.PerformanceStats.labels(mergedStats, False)

        statsFilename = f"{fold_stats_folder}/Stats-{str(date.today())}.txt"
        with open(statsFilename, "w") as writer:
            PrintStats(writer, mergedStats)

        statsFilename = f"{fold_stats_folder}/Errors-{str(date.today())}.txt"
        with open(statsFilename, "w") as writer:
            PrintErrorStats(writer, mergedStats.error_stats())
        
        statsFilename = f"{fold_stats_folder}/Stats-per-item-{str(date.today())}.txt"
        statsFilename2 = f"{fold_stats_folder}/Stats-per-item-label-{str(date.today())}.txt"

        # i = 0
        # with open(statsFilename, "w") as writer:
        #     with open(statsFilename2, "w") as writer2:
        #         for stats in fold_stats:
                        
        #             writer.write(f"Item #{i}\n")
        #             PrintStats(writer, stats)

        #             for label in expectedAndPredictedLabels:    
        #                 itemLabelStats = common.performance_metrics.PerformanceStats.stats_by_expected_or_predicted_label(mergedStats, label)
        #                 writer2.write(f"Item #{i} / {label}:")
        #                 PrintStats(writer2, itemLabelStats)
        #             i = i + 1
        statsFilename = f"{fold_stats_folder}/Stats-per-label-{str(date.today())}.txt";
        with open(statsFilename, "w") as writer:
            for label in expectedAndPredictedLabels:
            
                labelStats = common.performance_metrics.PerformanceStats.stats_by_expected_or_predicted_label(mergedStats, label);
                if label not in all_folds_per_expected_or_predicted_label_stats.keys():
                    all_folds_per_expected_or_predicted_label_stats[label] = []
                all_folds_per_expected_or_predicted_label_stats[label].append(labelStats)
                writer.write(f"{label}: ")
                PrintStats(writer, labelStats)
        
        for label in expectedLabels:
            labelStats = common.performance_metrics.PerformanceStats.stats_by_expected_label(mergedStats, label)
            if label not in all_folds_per_expected_label_stats.keys():
                all_folds_per_expected_label_stats[label] = []
            all_folds_per_expected_label_stats[label].append(labelStats)
        
    all_folds_merged_stats = common.performance_metrics.PerformanceStats.merge(all_folds_stats)
    
    merged_stats_filename = f"{merged_stats_folder}/Stats-{str(date.today())}.txt"
    with open(merged_stats_filename, "w") as writer:
        PrintAveragedStats(writer, all_folds_stats)
        

    merged_stats_filename = f"{merged_stats_folder}/Stats-per-label-{str(date.today())}.txt"
    with open(merged_stats_filename, "w") as writer:
        for label in all_folds_per_expected_label_stats.keys():
            writer.write(f"{label}: ")
            PrintAveragedStats(writer, all_folds_per_expected_label_stats[label])
            
    merged_stats_filename = f"{merged_stats_folder}/Errors-{str(date.today())}.txt"
    with open(merged_stats_filename, "w") as writer:
        PrintErrorStats(writer, all_folds_merged_stats.error_stats())

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(add_help=False)
    
    arg_parser.add_argument('--expected-folder', type=str, required= True)
    arg_parser.add_argument('--actual-folder', type=str, required= True)
    arg_parser.add_argument('--num-folds', type=int, required= True)
    arg_parser.add_argument('--stats-output-folder', type=str, required= True)

    args, _ = arg_parser.parse_known_args()

    actual_folders = args.actual_folder.split(',')
    expected_folders = args.expected_folder.split(',')
    merged_stats_folders = args.stats_output_folder.split(',')
    num_folds = int(args.num_folds)

    if len(actual_folders) != len(expected_folders):
        print("Missmatched number of actual/expected folders")
        exit

    for set_i in range(0, len(actual_folders)):
        actual_folder = actual_folders[set_i]
        expected_folder = expected_folders[set_i]
        merged_stats_folder = merged_stats_folders[set_i]
        if not os.path.exists(merged_stats_folder):
            os.makedirs(merged_stats_folder)
        
        print(f"Measuring performance in {expected_folder} - {actual_folder} (num.folds = {num_folds}, stats folder = {merged_stats_folders})")
        MeasurePerformanceFromFolder(expected_folder, actual_folder, num_folds, merged_stats_folder)

        