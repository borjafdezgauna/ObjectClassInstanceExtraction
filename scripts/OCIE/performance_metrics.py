

class SubEntityMatch:
    def __init__(self, expected_text=None, predicted_text=None, expected_label=None, predicted_label=None):
        self.expected_text = expected_text
        self.predicted_text = predicted_text
        self.expected_label = expected_label
        self.predicted_label = predicted_label


class CorrectSubEntity(SubEntityMatch):
    def __init__(self, text, label):
        super().__init__(expected_text=text, predicted_text=text, expected_label=label, predicted_label=label)


class SpuriousSubEntity(SubEntityMatch):
    def __init__(self, text, label):
        super().__init__(predicted_text=text, predicted_label=label)


class MissedSubEntity(SubEntityMatch):
    def __init__(self, text, label):
        super().__init__(expected_text=text, expected_label=label)


class IncorrectSubEntity(SubEntityMatch):
    def __init__(self, expected_text, predicted_text, expected_label, predicted_label):
        super().__init__(expected_text=expected_text, predicted_text=predicted_text,
                         expected_label=expected_label, predicted_label=predicted_label)


class PartialSubEntity(SubEntityMatch):
    def __init__(self, expected_text, predicted_text, expected_label, predicted_label):
        super().__init__(expected_text=expected_text, predicted_text=predicted_text,
                         expected_label=expected_label, predicted_label=predicted_label)


class EntityMatch:
    def __init__(self, item_id, expected_label=None, predicted_label=None):
        self.item_id = item_id
        self.expected_label = expected_label
        self.predicted_label = predicted_label
        self.correct = []
        self.partial = []
        self.incorrect = []
        self.spurious = []
        self.missed = []

    @property
    def num_sub_items(self):
        return len(self.correct) + len(self.partial) + len(self.incorrect) + len(self.spurious) + len(self.missed)

    @property
    def correct_ratio(self):
        return len(self.correct) / self.num_sub_items if self.num_sub_items > 0 else 0

    @property
    def incorrect_ratio(self):
        return len(self.incorrect) / self.num_sub_items if self.num_sub_items > 0 else 0

    @property
    def partial_ratio(self):
        return len(self.partial) / self.num_sub_items if self.num_sub_items > 0 else 0

    @property
    def missed_ratio(self):
        return len(self.missed) / self.num_sub_items if self.num_sub_items > 0 else 0

    @property
    def spurious_ratio(self):
        return len(self.spurious) / self.num_sub_items if self.num_sub_items > 0 else 0

    @property
    def possible_ratio(self):
        return self.correct_ratio + self.incorrect_ratio + self.partial_ratio + self.missed_ratio

    @property
    def actual_ratio(self):
        return self.correct_ratio + self.incorrect_ratio + self.partial_ratio + self.spurious_ratio


class PerformanceStats:
    def __init__(self):
        self.items = []

    @property
    def correct_ratio(self):
        return sum(item.correct_ratio for item in self.items) / len(self.items) if self.items else 0

    @property
    def partial_ratio(self):
        return sum(item.partial_ratio for item in self.items) / len(self.items) if self.items else 0

    @property
    def incorrect_ratio(self):
        return sum(item.incorrect_ratio for item in self.items) / len(self.items) if self.items else 0

    @property
    def missed_ratio(self):
        return sum(item.missed_ratio for item in self.items) / len(self.items) if self.items else 0

    @property
    def spurious_ratio(self):
        return sum(item.spurious_ratio for item in self.items) / len(self.items) if self.items else 0

    @property
    def precision(self):
        correct = sum(item.correct_ratio for item in self.items)
        actual = sum(item.actual_ratio for item in self.items)
        return correct / actual if actual > 0 else 0

    @property
    def recall(self):
        correct = sum(item.correct_ratio for item in self.items)
        possible = sum(item.possible_ratio for item in self.items)
        return correct / possible if possible > 0 else 0

    @property
    def f1(self):
        total = self.precision + self.recall
        return (2 * self.precision * self.recall) / total if total > 0 else 0

    @staticmethod
    def merge(stats_list):
        merged = PerformanceStats()
        for stats in stats_list:
            merged.items.extend(stats.items)
        return merged

    @staticmethod
    def stats_by_expected_or_predicted_label(stats, label):
        label_stats = PerformanceStats()
        for item in stats.items:
            if item.expected_label == label or item.predicted_label == label:
                label_stats.items.append(item)
        return label_stats

    @staticmethod
    def stats_by_expected_label(stats, label):
        label_stats = PerformanceStats()
        for item in stats.items:
            if item.expected_label == label or (item.expected_label and label in item.expected_label):
                label_stats.items.append(item)
        return label_stats

    @staticmethod
    def labels(stats, include_mismatches):
        labels = set()
        for item in stats.items:
            if item.expected_label and (include_mismatches or ',' not in item.expected_label):
                labels.add(item.expected_label)
            if item.predicted_label and (include_mismatches or ',' not in item.predicted_label):
                labels.add(item.predicted_label)
        return sorted(labels)

    def error_stats(self):
        errors = []
        for item in self.items:
            if item.expected_label != item.predicted_label:
                error_description = f"{item.expected_label}->{item.predicted_label}"
                label_error = next((e for e in errors if e['description'] == error_description), None)
                if not label_error:
                    label_error = {'description': error_description, 'num_items': 0}
                    errors.append(label_error)
                label_error['num_items'] += 1
            for sub_item in item.partial:
                if sub_item.expected_label != sub_item.predicted_label:
                    error_description = f"{item.expected_label}/{sub_item.expected_label}->{item.predicted_label}/{sub_item.predicted_label}"
                    label_error = next((e for e in errors if e['description'] == error_description), None)
                    if not label_error:
                        label_error = {'description': error_description, 'num_items': 0}
                        errors.append(label_error)
                    label_error['num_items'] += 1
        return errors
    
class PerformanceMetrics:
    
    @staticmethod
    def find_spurious_entities_in_range(item_id, predicted, start, end, stats):
        unexpected_entities = []

        if end >= 0:
            unexpected_entities = [
                prediction for prediction in predicted
                if prediction.start >= start and prediction.end <= end
            ]
        else:
            unexpected_entities = [
                prediction for prediction in predicted
                if prediction.start >= start
            ]

        for unexpected_entity in unexpected_entities:
            start = max(start, unexpected_entity.end + 1)
            spurious_entity = EntityMatch(item_id, None, unexpected_entity.name)
            for unexpected_sub_entity in unexpected_entity.subentities:
                spurious_sub_entity = SpuriousSubEntity(unexpected_entity.text, unexpected_sub_entity.name)
                spurious_entity.spurious.append(spurious_sub_entity)
            stats.items.append(spurious_entity)

        return start

    @staticmethod
    def match_entities(item_id, expected_entity, predicted_entities, stats, all_expected_entities):
        entity_match = EntityMatch(
            item_id,
            expected_entity.name,
            ",".join([pred.name for pred in predicted_entities])
        )

        for predicted_entity in predicted_entities:
            if predicted_entity.name == expected_entity.name:
                PerformanceMetrics.match_sub_entities(
                    item_id, expected_entity, predicted_entity, entity_match, all_expected_entities
                )
            else:
                for predicted_sub_entity in predicted_entity.subentities:
                    incorrect_sub_entity = IncorrectSubEntity(
                        "N/A", predicted_sub_entity.name, "N/A", predicted_sub_entity.text
                    )
                    entity_match.incorrect.append(incorrect_sub_entity)

        stats.items.append(entity_match)

    @staticmethod
    def match_sub_entities(item_id, expected_entity, predicted_entity, entity_match, all_expected_entities):
        processed_predicted_subentities = []

        for expected_sub_entity in expected_entity.subentities:
            overlapping_predictions = [
                prediction for prediction in predicted_entity.subentities
                if prediction.overlaps(expected_sub_entity)
            ]

            if not overlapping_predictions:
                missed_sub_entity = MissedSubEntity(expected_sub_entity.name, expected_sub_entity.text)
                entity_match.missed.append(missed_sub_entity)
            elif len(overlapping_predictions) > 1:
                for overlapping_prediction in overlapping_predictions:
                    if overlapping_prediction.name == expected_sub_entity.name:
                        partial_sub_entity = PartialSubEntity(
                            expected_sub_entity.text, overlapping_prediction.text,
                            expected_sub_entity.name, overlapping_prediction.name
                        )
                        entity_match.partial.append(partial_sub_entity)
                    else:
                        incorrect_sub_entity = IncorrectSubEntity(
                            expected_sub_entity.text, overlapping_prediction.text,
                            expected_sub_entity.name, overlapping_prediction.name
                        )
                        entity_match.incorrect.append(incorrect_sub_entity)
                    processed_predicted_subentities.append(overlapping_prediction)
            else:
                predicted_sub_entity = overlapping_predictions[0]
                if expected_sub_entity.name != predicted_sub_entity.name or expected_sub_entity.text != predicted_sub_entity.text:
                    incorrect_sub_entity = IncorrectSubEntity(
                        expected_sub_entity.text, predicted_sub_entity.text,
                        expected_sub_entity.name, predicted_sub_entity.name
                    )
                    entity_match.incorrect.append(incorrect_sub_entity)
                else:
                    correct_sub_entity = CorrectSubEntity(expected_sub_entity.text, expected_sub_entity.name)
                    entity_match.correct.append(correct_sub_entity)
                processed_predicted_subentities.append(predicted_sub_entity)

        for predicted_sub_entity in predicted_entity.subentities:
            if predicted_sub_entity not in processed_predicted_subentities:
                expected_sub_entity_parent = next(
                    (entity for entity in all_expected_entities
                     if entity != expected_entity and entity.start <= predicted_sub_entity.start and entity.end >= predicted_sub_entity.end),
                    None
                )
                if not expected_sub_entity_parent:
                    spurious_sub_entity = SpuriousSubEntity(predicted_sub_entity.text, predicted_sub_entity.name)
                    entity_match.spurious.append(spurious_sub_entity)


    @staticmethod
    def match_entities(item_id, expected_entity, predicted_entities, stats, all_expected_entities):
        entity_match = EntityMatch(
            item_id,
            expected_entity.name,
            ",".join([pred.name for pred in predicted_entities])
        )

        for predicted_entity in predicted_entities:
            if predicted_entity.name == expected_entity.name:
                PerformanceMetrics.match_sub_entities(
                    item_id, expected_entity, predicted_entity, entity_match, all_expected_entities
                )
            else:
                for predicted_sub_entity in predicted_entity.subentities:
                    incorrect_sub_entity = IncorrectSubEntity(
                        "N/A", predicted_sub_entity.name, "N/A", predicted_sub_entity.text
                    )
                    entity_match.incorrect.append(incorrect_sub_entity)

        stats.items.append(entity_match)

    @staticmethod
    def match_sub_entities(item_id, expected_entity, predicted_entity, entity_match, all_expected_entities):
        processed_predicted_subentities = []

        for expected_sub_entity in expected_entity.subentities:
            overlapping_predictions = expected_sub_entity.overlaps(predicted_entity.subentities)

            if not overlapping_predictions:
                missed_sub_entity = MissedSubEntity(expected_sub_entity.name, expected_sub_entity.text)
                entity_match.missed.append(missed_sub_entity)
            elif len(overlapping_predictions) > 1:
                for overlapping_prediction in overlapping_predictions:
                    if overlapping_prediction.name == expected_sub_entity.name:
                        partial_sub_entity = PartialSubEntity(
                            expected_sub_entity.text, overlapping_prediction.text,
                            expected_sub_entity.name, overlapping_prediction.name
                        )
                        entity_match.partial.append(partial_sub_entity)
                    else:
                        incorrect_sub_entity = IncorrectSubEntity(
                            expected_sub_entity.text, overlapping_prediction.text,
                            expected_sub_entity.name, overlapping_prediction.name
                        )
                        entity_match.incorrect.append(incorrect_sub_entity)
                    processed_predicted_subentities.append(overlapping_prediction)
            else:
                predicted_sub_entity = overlapping_predictions[0]
                if expected_sub_entity.name != predicted_sub_entity.name or expected_sub_entity.text != predicted_sub_entity.text:
                    incorrect_sub_entity = IncorrectSubEntity(
                        expected_sub_entity.text, predicted_sub_entity.text,
                        expected_sub_entity.name, predicted_sub_entity.name
                    )
                    entity_match.incorrect.append(incorrect_sub_entity)
                else:
                    correct_sub_entity = CorrectSubEntity(expected_sub_entity.text, expected_sub_entity.name)
                    entity_match.correct.append(correct_sub_entity)
                processed_predicted_subentities.append(predicted_sub_entity)

        for predicted_sub_entity in predicted_entity.subentities:
            if predicted_sub_entity not in processed_predicted_subentities:
                expected_sub_entity_parent = next(
                    (entity for entity in all_expected_entities
                     if entity != expected_entity and entity.start <= predicted_sub_entity.start and entity.end >= predicted_sub_entity.end),
                    None
                )
                if not expected_sub_entity_parent:
                    spurious_sub_entity = SpuriousSubEntity(predicted_sub_entity.text, predicted_sub_entity.name)
                    entity_match.spurious.append(spurious_sub_entity)

    @staticmethod
    def calculate(expected, predicted, item_id):
        stats = PerformanceStats()
        start = 0

        if expected.entities:
            for expected_entity in expected.entities:
                start = PerformanceMetrics.find_spurious_entities_in_range(
                    item_id, predicted.entities, start, expected_entity.start - 1, stats
                )

                overlapping_predictions = expected_entity.overlaps(predicted.entities, start)

                if not overlapping_predictions:
                    missed_entity = EntityMatch(item_id, expected_entity.name, None)
                    for expected_sub_entity in expected_entity.subentities:
                        missed_sub_entity = MissedSubEntity(expected_sub_entity.text, expected_sub_entity.name)
                        missed_entity.missed.append(missed_sub_entity)
                    stats.items.append(missed_entity)
                    start = max(start, expected_entity.end + 1)
                elif len(overlapping_predictions) > 1:
                    PerformanceMetrics.match_entities(
                        item_id, expected_entity, overlapping_predictions, stats, expected.entities
                    )
                    start = max(start, overlapping_predictions[-1].end + 1)
                else:
                    predicted_entity = overlapping_predictions[0]
                    if expected_entity.name != predicted_entity.name:
                        incorrect_entity = EntityMatch(item_id, expected_entity.name, predicted_entity.name)
                        for expected_sub_entity in expected_entity.subentities:
                            incorrect_sub_entity = IncorrectSubEntity(
                                expected_sub_entity.text, None, expected_sub_entity.name, None
                            )
                            incorrect_entity.incorrect.append(incorrect_sub_entity)
                        stats.items.append(incorrect_entity)
                    else:
                        entity_match = EntityMatch(item_id, expected_entity.name, predicted_entity.name)
                        PerformanceMetrics.match_sub_entities(
                            item_id, expected_entity, predicted_entity, entity_match, expected.entities
                        )
                        stats.items.append(entity_match)
                    start = max(start, predicted_entity.end + 1)

            PerformanceMetrics.find_spurious_entities_in_range(item_id, predicted.entities, start, -1, stats)
            
        else:
            
            #Add all predicted entities as spurious
            for predictedEntity in predicted.entities:
            
                spuriousEntity = EntityMatch(item_id, None, predictedEntity.name)
                for predictedSubEntity in predictedEntity.subentities:
                    
                
                    spuriousSubEntity = SpuriousSubEntity(predictedSubEntity.text, predictedSubEntity.name)
                    spuriousEntity.spurious.append(spuriousSubEntity)
                
                stats.items.append(spuriousEntity)
            
            

        return stats