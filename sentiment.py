"""
CS311 Programming Assignment 4: Naive Bayes

Full Name: Frank Bautista

Brief description of my custom classifier:

I believe the Naive Bayes model we have constructed does an ok job at predicting sentiment.
However i believe it will always do a horrible job at predicting sentiment when there is a negating word in the sentence.
For example: I do not like this movie. Most of the sentence is positive but the word "not" makes the sentence negative.
I believe the model could do a better job at predicting sentiment if it could take into account negating words, possibly getting rid of 
connecting words like "is" "and" etc... and only focusing on the main words that most likely determine sentiment. Most of these connecting words
are short in length, so i believe it may be possible to remove a significant portion by having a word limit of 2-4 characters (as long as its not a  common negating word).

(not yet implemented)
"""
import argparse, math, os, re, string, zipfile
from typing import Generator, Hashable, Iterable, List, Sequence, Tuple
import numpy as np
from sklearn import metrics



class Sentiment:
    """Naive Bayes model for predicting text sentiment"""

    def __init__(self, labels: Iterable[Hashable]):
        """Create a new sentiment model

        Args:
            labels (Iterable[Hashable]): Iterable of potential labels in sorted order.
        """
        self.positive_documents_count = 0
        self.negative_documents_count = 0
        self.positive_words_frequencies = {}
        self.negative_words_frequencies = {}
        self.total_positive_words = 0
        self.total_negative_words = 0
        self.labels = labels


    def preprocess(self, example: str, id:str =None) -> List[str]:
        """Normalize the string into a list of words.

        Args:
            example (str): Text input to split and normalize
            id (str, optional): File name from training/test data (may not be available). Defaults to None.

        Returns:
            List[str]: Normalized words
        """

        example = example.lower()
        example = example.translate(str.maketrans('', '', string.punctuation)) # remove punctuation
        example = example.strip() # remove leading and trailing whitespaces
        return example.split()

    def add_example(self, example: str, label: Hashable, id:str = None):
        """Add a single training example with label to the model

        Args:
            example (str): Text input
            label (Hashable): Example label
            id (str, optional): File name from training/test data (may not be available). Defaults to None.
        """
        # TODO: Implement function to update the model with words identified in this training example
        stripped_example = self.preprocess(example)
        if label == 1:
            self.positive_documents_count += 1
            for word in stripped_example:
                self.total_positive_words += 1
                if word in self.positive_words_frequencies:
                    self.positive_words_frequencies[word] += 1
                else:
                    self.positive_words_frequencies[word] = 1
        elif label == 0:
            self.negative_documents_count += 1
            for word in stripped_example:
                self.total_negative_words += 1
                if word in self.negative_words_frequencies:
                    self.negative_words_frequencies[word] += 1
                else:
                    self.negative_words_frequencies[word] = 1



    def predict(self, example: str, pseudo=0.0001, id:str = None) -> Sequence[float]:
        """Predict the P(label|example) for example text, return probabilities as a sequence

        Args:
            example (str): Test input
            pseudo (float, optional): Pseudo-count for Laplace smoothing. Defaults to 0.0001.
            id (str, optional): File name from training/test data (may not be available). Defaults to None.

        Returns:
            Sequence[float]: Probabilities in order of originally provided labels
        """
        stripped_example = self.preprocess(example)
        prior_positive = math.log(self.positive_documents_count / (self.positive_documents_count + self.negative_documents_count))
        prior_negative = math.log(self.negative_documents_count / (self.positive_documents_count + self.negative_documents_count))
        positive_conditional_probability = self.conditional_probability(stripped_example, 1, pseudo)
        negative_conditional_probability = self.conditional_probability(stripped_example, 0, pseudo)
        naive_bayes_denominator = np.logaddexp( (prior_positive + positive_conditional_probability), (prior_negative + negative_conditional_probability) ) 
        
        #P(positive|example)
        # plus is multiplication in log space (log(a) + log(b) = log(a*b))
        # minus is division in log space (log(a) - log(b) = log(a/b))
        positive_probability = math.exp( (prior_positive + positive_conditional_probability) - naive_bayes_denominator)

        #P(negative|example)
        negative_probability = math.exp( (prior_negative + negative_conditional_probability) - naive_bayes_denominator )
        
        return [negative_probability, positive_probability]

    def conditional_probability(self, words, sentiment, pseudo=0.0001) -> float:
        """
        Given a list of words, find the conditional probability of the features (words) given the sentiment using the Naive Bayes model.

        Args:
            words (list): list of preprocessed words. The features.
            sentiment (int): the sentiment to calculate the conditional probability for. 0 for negative, 1 for positive
            pseudo (float): Pseudo-count for Laplace smoothing. Defaults to 0.0001.
        
        Returns:
            float: the conditional probability of the features given the sentiment. (log probability to avoid underflow)

        """
        accumulation_of_probabilities = 0

        if sentiment == 1:
            for word in words:
                #using math.log to avoid underflow
                accumulation_of_probabilities += math.log((self.positive_words_frequencies.get(word, 0) + pseudo) / (self.total_positive_words + (pseudo * len(self.positive_words_frequencies))))
        elif sentiment == 0:
            for word in words:
                accumulation_of_probabilities += math.log((self.negative_words_frequencies.get(word, 0) + pseudo) / (self.total_negative_words + (pseudo * len(self.negative_words_frequencies) )))
        return accumulation_of_probabilities

class CustomSentiment(Sentiment):
    # TODO: Implement your custom Naive Bayes model
    def __init__(self, labels: Iterable[Hashable]):
        super().__init__(labels)



def process_zipfile(filename: str) -> Generator[Tuple[str, str, int], None, None]:
    """Create generator of labeled examples from a Zip file that yields a tuple with
    the id (filename of input), text snippet and label (0 or 1 for negative and positive respectively).

    You can use the generator as a loop sequence, e.g.

    for id, example, label in process_zipfile("test.zip"):
        # Do something with example and label

    Args:
        filename (str): Name of zip file to extract examples from

    Yields:
        Generator[Tuple[str, str, int], None, None]: Tuple of (id, example, label)
    """
    with zipfile.ZipFile(filename) as zip:
        for info in zip.infolist():
            # Iterate through all file entries in the zip file, picking out just those with specific ratings
            match = re.fullmatch(r"[^-]+-(\d)-\d+.txt", os.path.basename(info.filename))
            if not match or (match[1] != "1" and match[1] != "5"):
                # Ignore all but 1 or 5 ratings
                continue
            # Extract just the relevant file the Zip archive and yield a tuple
            with zip.open(info.filename) as file:
                yield (
                    match[0],
                    file.read().decode("utf-8", "ignore"),
                    1 if match[1] == "5" else 0,
                )


def compute_metrics(y_true, y_pred):
    """Compute metrics to evaluate binary classification accuracy

    Args:
        y_true: Array-like ground truth (correct) target values.
        y_pred: Array-like estimated targets as returned by a classifier.

    Returns:
        dict: Dictionary of metrics in including confusion matrix, accuracy, recall, precision and F1
    """
    return {
        "confusion": metrics.confusion_matrix(y_true, y_pred),
        "accuracy": metrics.accuracy_score(y_true, y_pred),
        "recall": metrics.recall_score(y_true, y_pred),
        "precision": metrics.precision_score(y_true, y_pred),
        "f1": metrics.f1_score(y_true, y_pred),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Naive Bayes sentiment analyzer")

    parser.add_argument(
        "--train",
        default="data/train.zip",
        help="Path to zip file or directory containing training files.",
    )
    parser.add_argument(
        "--test",
        default="data/test.zip",
        help="Path to zip file or directory containing testing files.",
    )
    parser.add_argument(
        "-m", "--model", default="base", help="Model to use: One of base or custom"
    )
    parser.add_argument("example", nargs="?", default=None)

    args = parser.parse_args()

    # Train model
    if args.model == "custom":
        model = CustomSentiment(labels=[0, 1])
    else:
        model = Sentiment(labels=[0, 1])
    for id, example, y_true in process_zipfile(
        os.path.join(os.path.dirname(__file__), args.train)
    ):
        model.add_example(example, y_true, id=id)

    # If interactive example provided, compute sentiment for that example
    if args.example:
        print(model.predict(args.example))
    else:
        predictions = []
        for id, example, y_true in process_zipfile(
            os.path.join(os.path.dirname(__file__), args.test)
        ):
            # Determine the most likely class from predicted probabilities
            predictions.append((id, y_true, np.argmax(model.predict(example,id=id))))

        # Compute and print accuracy metrics
        _, y_test, y_true = zip(*predictions)
        predict_metrics = compute_metrics(y_test, y_true)
        for met, val in predict_metrics.items():
            print(
                f"{met.capitalize()}: ",
                ("\n" if isinstance(val, np.ndarray) else ""),
                val,
                sep="",
            )

