using System;
using System.Collections.Generic;
using static Xerkariak.Utils.Logger;

namespace Xerkariak.Ner
{
    public class ErrorStats
    {
        public string Description { get; set; }
        public int NumItems { get; set; }
    }

    public abstract class SubEntityMatch
    {
        public string ExpectedText { get; protected set; }
        public string PredictedText { get; protected set; }
        public string ExpectedLabel { get; protected set; }
        public string PredictedLabel { get; protected set; }
    }

    public class CorrectSubEntity : SubEntityMatch
    {
        public CorrectSubEntity(string text, string label)
        {
            PredictedText = text;
            ExpectedText = text;
            PredictedLabel = label;
            ExpectedLabel = label;
        }
    }

    public class SpuriousSubEntity : SubEntityMatch
    {
        public SpuriousSubEntity(string text, string label)
        {
            PredictedText = text;
            PredictedLabel = label;
        }
    }

    public class MissedSubEntity : SubEntityMatch
    {
        public MissedSubEntity(string text, string label)
        {
            ExpectedText = text;
            ExpectedLabel = label;
        }
    }

    public class IncorrectSubEntity : SubEntityMatch
    {
        public IncorrectSubEntity(string expectedText, string predictedText, string expectedLabel, string predictedLabel)
        {
            ExpectedText = expectedText;
            PredictedText = predictedText;
            ExpectedLabel = expectedLabel;
            PredictedLabel = predictedLabel;
        }
    }

    public class PartialSubEntity : SubEntityMatch
    {
        public PartialSubEntity(string expectedText, string predictedText, string expectedLabel, string predictedLabel)
        {
            ExpectedText = expectedText;
            PredictedText = predictedText;
            ExpectedLabel = expectedLabel;
            PredictedLabel = predictedLabel;
        }
    }

    public class EntityMatch
    {
        public string ExpectedLabel { get; protected set; }
        public string PredictedLabel { get; protected set; }
        public List<CorrectSubEntity> Correct { get; set; } = new List<CorrectSubEntity>();
        public List<PartialSubEntity> Partial { get; set; } = new List<PartialSubEntity>();
        public List<IncorrectSubEntity> Incorrect { get; set; } = new List<IncorrectSubEntity>();
        public List<SpuriousSubEntity> Spurious { get; set; } = new List<SpuriousSubEntity>();
        public List<MissedSubEntity> Missed { get; set; } = new List<MissedSubEntity>();

        public int NumSubItems
        {
            get
            {
                return Correct.Count + Partial.Count + Incorrect.Count + Spurious.Count + Missed.Count;
            }
        }
        public double CorrectRatio
        {
            get
            {
                double numSubItems = NumSubItems;
                if (numSubItems == 0)
                    return 0;
                return Correct.Count / numSubItems;
            }
        }
        public double IncorrectRatio
        {
            get
            {
                double numSubItems = NumSubItems;
                if (numSubItems == 0)
                    return 0;
                return Incorrect.Count / numSubItems;
            }
        }
        public double PartialRatio
        {
            get
            {
                double numSubItems = NumSubItems;
                if (numSubItems == 0)
                    return 0;
                return Partial.Count / numSubItems;
            }
        }

        public double MissedRatio
        {
            get
            {
                double numSubItems = NumSubItems;
                if (numSubItems == 0)
                    return 0;
                return Missed.Count / numSubItems;
            }
        }

        public double SpuriousRatio
        {
            get
            {
                double numSubItems = NumSubItems;
                if (numSubItems == 0)
                    return 0;
                return Spurious.Count / numSubItems;
            }
        }

        public double PossibleRatio
        {
            get
            {
                return CorrectRatio + IncorrectRatio + PartialRatio + MissedRatio;
            }
        }

        public double ActualRatio
        {
            get
            {
                return CorrectRatio + IncorrectRatio + PartialRatio + SpuriousRatio;
            }
        }
        public string ItemId { get; private set; }

        public ItemType Type { get; private set; }

        public EntityMatch(string itemId, string expectedLabel, string predictedLabel)
        {
            ItemId = itemId;
            ExpectedLabel = expectedLabel;
            PredictedLabel = predictedLabel;
        }
    }
    public class PerformanceStats
    {
        public List<EntityMatch> Items { get; set; } = new List<EntityMatch>();

        public double CorrectRatio
        {
            get
            {
                if (Items.Count == 0)
                    return 0;
                double ratio = 0;
                foreach (var item in Items)
                    ratio += item.CorrectRatio;
                return ratio / (double)Items.Count;
            }
        }

        public double PartialRatio
        {
            get
            {
                if (Items.Count == 0)
                    return 0;
                double ratio = 0;
                foreach (var item in Items)
                    ratio += item.PartialRatio;
                return ratio / (double)Items.Count;
            }
        }

        public double IncorrectRatio
        {
            get
            {
                if (Items.Count == 0) return 0;
                double ratio = 0;
                foreach (var item in Items)
                    ratio += item.IncorrectRatio;
                return ratio / (double)Items.Count;
            }
        }

        public double MissedRatio
        {
            get
            {
                if (Items.Count == 0) return 0;
                double ratio = 0;
                foreach (var item in Items)
                    ratio += item.MissedRatio;
                return ratio / (double)Items.Count;
            }
        }

        public double SpuriousRatio
        {
            get
            {
                if (Items.Count == 0) return 0;
                double ratio = 0;
                foreach (var item in Items)
                    ratio += item.SpuriousRatio;
                return ratio / (double)Items.Count;
            }
        }

        public double Precision
        {
            get 
            {
                double correct = 0;
                double actual = 0;
                foreach (var item in Items)
                {
                    correct += item.CorrectRatio;
                    actual += item.ActualRatio;
                }
                if (actual == 0)
                    return 0;
                return correct / actual;
            }
        }
        public double Recall
        {
            get
            {
                double correct = 0;
                double possible = 0;
                foreach (var item in Items)
                {
                    correct += item.CorrectRatio;
                    possible += item.PossibleRatio;
                }
                if (possible == 0)
                    return 0;
                return correct / possible;
            }
        }
        public double F1
        {
            get
            {
                double total = Precision + Recall;
                if (total == 0)
                    return 0;
                return (2 * Precision * Recall) / total;
            }
        }


        public static PerformanceStats Merge(List<PerformanceStats> stats)
        {
            PerformanceStats merged = new PerformanceStats();

            foreach (PerformanceStats stat in stats)
                merged.Items.AddRange(stat.Items);

            return merged;
        }
        

        public static PerformanceStats StatsByExpectedOrPredictedLabel(PerformanceStats stats, string label)
        {
            PerformanceStats labelStats = new PerformanceStats();
            foreach (EntityMatch item in stats.Items)
            {
                if (item.ExpectedLabel == label || item.PredictedLabel == label)
                    labelStats.Items.Add(item);
            }

            return labelStats;
        }

        public static PerformanceStats StatsByExpectedLabel(PerformanceStats stats, string label)
        {
            PerformanceStats labelStats = new PerformanceStats();
            foreach (EntityMatch item in stats.Items)
            {
                if (item.ExpectedLabel == label || (item.ExpectedLabel != null && item.ExpectedLabel.Contains(label)))
                    labelStats.Items.Add(item);
            }

            return labelStats;
        }

        public static List<string> Labels(PerformanceStats stats, bool includeMissmatches)
        {
            List<string> labels = new List<string>();

            foreach (EntityMatch item in stats.Items)
            {
                if (item.ExpectedLabel != null && !labels.Contains(item.ExpectedLabel) &&
                    (!item.ExpectedLabel.Contains(',') || includeMissmatches))
                    labels.Add(item.ExpectedLabel);
                if (item.PredictedLabel != null && !labels.Contains(item.PredictedLabel) &&
                    (!item.PredictedLabel.Contains(',') || includeMissmatches))
                    labels.Add(item.PredictedLabel);
            }

            labels.Sort((x, y) => x.CompareTo(y));
            return labels;
        }

        public List<ErrorStats> ErrorStats()
        {
            List<ErrorStats> errors = new List<ErrorStats>();

            foreach (EntityMatch item in Items)
            {
                if (item.ExpectedLabel != item.PredictedLabel)
                {
                    string errorDescription = $"{item.ExpectedLabel}->{item.PredictedLabel}";
                    ErrorStats labelError = errors.Find(error => error.Description == errorDescription);
                    if (labelError == null)
                    {
                        labelError = new ErrorStats() { Description = errorDescription };
                        errors.Add(labelError);
                    }
                    labelError.NumItems++;
                }
                foreach (PartialSubEntity subItem in item.Partial)
                {
                    if (subItem.ExpectedLabel != subItem.PredictedLabel)
                    {
                        string errorDescription = $"{item.ExpectedLabel}/{subItem.ExpectedLabel}->{item.PredictedLabel}/{subItem.PredictedLabel}";
                        ErrorStats labelError = errors.Find(error => error.Description == errorDescription);
                        if (labelError == null)
                        {
                            labelError = new ErrorStats() { Description = errorDescription };
                            errors.Add(labelError);
                        }
                        labelError.NumItems++;
                    }
                }
            }

            return errors;
        }
    }
    public static class PerformanceMetrics
    {
        private static int FindSpuriousEntitiesInRange(string itemId, List<Entity> predicted, int start, int end, PerformanceStats stats)
        {
            List<Entity> unexpectedEntities = null;

            if (end != 0)
            {
                unexpectedEntities = predicted.FindAll(prediction =>
                    (prediction.Start >= start && prediction.End <= end));// ||
                    //(prediction.End >= start && prediction.End <= end) ||
                    //(prediction.Start <= start && prediction.End >= end));
            }
            else
            {
                unexpectedEntities = predicted.FindAll(prediction =>
                    prediction.Start >= start);
            }
            
            foreach (Entity unexpectedEntity in unexpectedEntities)
            {
                start = Math.Max(start, unexpectedEntity.End + 1);
                EntityMatch spuriousEntity = new EntityMatch(itemId, null, unexpectedEntity.Name);
                foreach (SubEntity unexpectedSubEntity in unexpectedEntity.SubEntities)
                {
                    SpuriousSubEntity spuriousSubEntity = new SpuriousSubEntity(unexpectedEntity.Text, unexpectedSubEntity.Name);
                    spuriousEntity.Spurious.Add(spuriousSubEntity);
                }
                stats.Items.Add(spuriousEntity);
            }
            return start;
        }
        private static void MatchEntities(string itemId, Entity expectedEntity, List<Entity> predictedEntities, PerformanceStats stats,
            List<Entity> allExpectedEntities)
        {
            EntityMatch entityMatch = new EntityMatch(itemId, expectedEntity.Name,
                Utils.Strings.AsCommaSeparatedValues(predictedEntities, (pred) =>pred.Name, ',', true));

            foreach (var predictedEntity in predictedEntities)
            {
                if (predictedEntity.Name == expectedEntity.Name)
                    MatchSubEntities(itemId, expectedEntity, predictedEntity, entityMatch, allExpectedEntities);
                else
                {
                    foreach (SubEntity predictedSubEntity in predictedEntity.SubEntities)
                    {
                        IncorrectSubEntity incorrectSubEntity = new IncorrectSubEntity("N/A", predictedSubEntity.Name, "N/A", predictedSubEntity.Value);
                        entityMatch.Incorrect.Add(incorrectSubEntity);
                    }
                }
            }
            entityMatch.Missed = Utils.Lists.RemoveDuplicates(entityMatch.Missed);

            stats.Items.Add(entityMatch);
        }
        private static void MatchSubEntities(string itemId, Entity expectedEntity, Entity predictedEntity, EntityMatch entityMatch,
            List<Entity> allExpectedEntities)
        {
            List<SubEntity> processedPredictedSubentities = new List<SubEntity>();

            for (int i = 0; i < expectedEntity.SubEntities.Count; i++)
            {
                SubEntity expectedSubEntity = expectedEntity.SubEntities[i];

                List<SubEntity> overlappingPredictions = expectedSubEntity.Overlaps(predictedEntity.SubEntities);
                    //predictedEntity.SubEntities.FindAll(prediction =>
                    //(prediction.Start >= expectedSubEntity.Start && prediction.Start <= expectedSubEntity.End) ||
                    //(prediction.End >= expectedSubEntity.Start && prediction.End <= expectedSubEntity.End) ||
                    //(prediction.Start <= expectedSubEntity.Start && prediction.End >= expectedSubEntity.End));
                if (overlappingPredictions.Count == 0)
                {
                    //Completely missed subentity: mark it as false negatives
                    MissedSubEntity missedSubEntity = new MissedSubEntity(expectedSubEntity.Name, expectedSubEntity.Value);
                    entityMatch.Missed.Add(missedSubEntity);
                }
                else if (overlappingPredictions.Count > 1)
                {
                    //More than one entity predicted: a) mark expected sub-entities as false negatives
                    foreach(var overlappingPrediction in overlappingPredictions)
                    {
                        if (overlappingPrediction.Name == expectedSubEntity.Name)
                        {
                            PartialSubEntity partialSubEntity = new PartialSubEntity(expectedSubEntity.Value, overlappingPrediction.Value,
                                expectedSubEntity.Name, overlappingPrediction.Name);
                            entityMatch.Partial.Add(partialSubEntity);
                        }
                        else
                        {
                            IncorrectSubEntity incorrectSubEntity = new IncorrectSubEntity(expectedSubEntity.Value, overlappingPrediction.Value,
                                expectedSubEntity.Name, overlappingPrediction.Name);
                            entityMatch.Incorrect.Add(incorrectSubEntity);
                        }
                        processedPredictedSubentities.Add(overlappingPrediction);
                    }
                }
                else if (overlappingPredictions.Count == 1)
                {
                    SubEntity predictedSubEntity = overlappingPredictions[0];
                    if (expectedSubEntity.Name != predictedSubEntity.Name || expectedSubEntity.Value != predictedSubEntity.Value)
                    {
                        //Wrong entity label: a) mark expected sub-entity as incorrect
                        IncorrectSubEntity incorrectSubEntity = new IncorrectSubEntity(expectedSubEntity.Value, predictedSubEntity.Value,
                                expectedSubEntity.Name, predictedSubEntity.Name);
                        entityMatch.Incorrect.Add(incorrectSubEntity);
                    }
                    else
                    {
                        //Correct sub-entity: add as true positive
                        CorrectSubEntity correctSubEntity = new CorrectSubEntity(expectedSubEntity.Value, expectedSubEntity.Name);
                        entityMatch.Correct.Add(correctSubEntity);
                    }
                    processedPredictedSubentities.Add(predictedSubEntity);
                }
            }
            foreach (SubEntity predictedSubEntity in predictedEntity.SubEntities)
            {
                if (!processedPredictedSubentities.Contains(predictedSubEntity))
                {
                    //Check that this predicted subentitiy is not part of any other expected entity
                    //If this subentity should have been inside a different expected entity, we don't count it.
                    //It will be counted when matched with the expected parent
                    Entity expectedSubEntityParent = allExpectedEntities.Find(entity =>
                        entity != expectedEntity && entity.Start <= predictedSubEntity.Start && entity.End >= predictedSubEntity.End);
                    if (expectedSubEntityParent == null)
                    {
                        SpuriousSubEntity spuriousSubEntity = new SpuriousSubEntity(predictedSubEntity.Value, predictedSubEntity.Name);
                        entityMatch.Spurious.Add(spuriousSubEntity);
                    }
                }
            }
        }

        

        public static PerformanceStats Calculate(NerResult expected, NerResult predicted, string itemId)
        {
            PerformanceStats stats = new PerformanceStats();

            int start = 0;

            if (expected.Entities.Count > 0)
            {

                for (int i = 0; i < expected.Entities.Count; i++)
                {
                    Entity expectedEntity = expected.Entities[i];
                    start = FindSpuriousEntitiesInRange(itemId, predicted.Entities, start, expectedEntity.Start - 1, stats);
                    //start = expectedEntity.End + 1;

                    List<Entity> overlappingPredictions = expectedEntity.Overlaps(predicted.Entities, start);

                    if (overlappingPredictions.Count == 0)
                    {
                        //Completely missed entity: mark all expected sub-entities as false negatives
                        EntityMatch missedEntity = new EntityMatch(itemId, expectedEntity.Name, null);
                        foreach (SubEntity expectedSubEntity in expectedEntity.SubEntities)
                        {
                            MissedSubEntity missedSubEntity = new MissedSubEntity(expectedSubEntity.Value, expectedSubEntity.Name);
                            missedEntity.Missed.Add(missedSubEntity);
                        }
                        stats.Items.Add(missedEntity);
                        start = Math.Max(start, expectedEntity.End + 1);
                    }
                    else if (overlappingPredictions.Count > 1)
                    {
                        //More than one entity predicted: match overlapping predictions with expected entity
                        MatchEntities(itemId, expectedEntity, overlappingPredictions, stats, expected.Entities);
                        start = Math.Max(start, overlappingPredictions[overlappingPredictions.Count - 1].End + 1);
                    }
                    else if (overlappingPredictions.Count == 1)
                    {
                        Entity predictedEntity = overlappingPredictions[0];
                        if (expectedEntity.Name != predictedEntity.Name)
                        {
                            EntityMatch incorrectEntity = new EntityMatch(itemId, expectedEntity.Name, predictedEntity.Name);
                            //Wrong entity label: a) mark expected entity as incorrect
                            foreach (SubEntity expectedSubEntity in expectedEntity.SubEntities)
                            {
                                IncorrectSubEntity incorrectSubEntity = new IncorrectSubEntity(expectedSubEntity.Value, null, expectedSubEntity.Value, null);
                                incorrectEntity.Incorrect.Add(incorrectSubEntity);
                            }
                            stats.Items.Add(incorrectEntity);
                        }
                        else
                        {
                            //Correct entity label: check subentities
                            EntityMatch entityMatch = new EntityMatch(itemId, expectedEntity.Name, predictedEntity.Name);
                            MatchSubEntities(itemId, expectedEntity, predictedEntity, entityMatch, expected.Entities);
                            stats.Items.Add(entityMatch);
                        }
                        start = Math.Max(start, predictedEntity.End + 1);
                    }
                }

                //Any unexpected prediction after the last expected entity?
                FindSpuriousEntitiesInRange(itemId, predicted.Entities, start, 0, stats);
            }
            else
            {
                //Add all predicted entities as spurious
                foreach (Entity predictedEntity in predicted.Entities)
                {
                    EntityMatch spuriousEntity = new EntityMatch(itemId, null, predictedEntity.Name);
                    foreach (var predictedSubEntity in predictedEntity.SubEntities)
                    {
                        SpuriousSubEntity spuriousSubEntity = new SpuriousSubEntity(predictedSubEntity.Value, predictedSubEntity.Name);
                        spuriousEntity.Spurious.Add(spuriousSubEntity);
                    }
                    stats.Items.Add(spuriousEntity);
                }
            }

            return stats;
        }

        public static string CombineLabels(string annotationLabel, string subAnnotationLabel)
        {
            return $"{annotationLabel}/{subAnnotationLabel}";
        }
    }
}