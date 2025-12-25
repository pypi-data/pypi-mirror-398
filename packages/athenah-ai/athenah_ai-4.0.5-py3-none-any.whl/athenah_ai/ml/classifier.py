import os
import pickle
import json
import logging
from typing import List, Dict, Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report

# Setup a basic logger
logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)

# Define the base directory (current directory for simplicity)
basedir = os.getcwd()


class MLClassifier:
    """
    MLClassifier class for a retrieval-based chatbot using RandomForestClassifier.
    """

    df: pd.DataFrame = None

    def __init__(
        cls,
        storage_type: str,
        id: str,
        dir: str,
        name: str,
        version: str = "v1",
        features: List[str] = [],
    ) -> None:
        """
        Initializes the MLClassifier chatbot.

        Parameters:
        - storage_type (str): Type of storage ('local' or 'gcs').
        - id (str): Identifier for the chatbot.
        - dir (str): Directory to store model and related files.
        - name (str): Name of the chatbot.
        - version (str): Version of the chatbot.
        - features (List[str]): List of feature names (e.g., ['user_input']).
        """
        cls.label_encoder = LabelEncoder()
        cls.features = features
        cls.storage_type = storage_type
        cls.id = id
        cls.dir = dir
        cls.name = name
        cls.version = version
        cls.dist_path: str = os.path.join(basedir, "dist")
        cls.base_path: str = os.path.join(cls.dist_path, dir)
        cls.name_path: str = os.path.join(cls.base_path, f"{cls.name}-ml")
        os.makedirs(cls.base_path, exist_ok=True)
        os.makedirs(cls.name_path, exist_ok=True)

        # Initialize empty data.json if not present
        data_json_path = os.path.join(cls.name_path, "data.json")
        if not os.path.isfile(data_json_path):
            with open(data_json_path, "w") as f:
                f.write("[]")

        # Initialize placeholders
        cls.model = None
        cls.vectorizer = None
        cls.vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=1000)
        cls.label_encoder_values = {}

    def load_data(cls, qa_pairs: List[Dict[str, str]] = None) -> pd.DataFrame:
        """
        Loads the dataset from a list of question-answer pairs.

        Parameters:
        - qa_pairs (List[Dict[str, str]]): List of dictionaries with 'question' and 'answer' keys.

        Returns:
        - pd.DataFrame: Loaded DataFrame.
        """
        try:
            logger.debug(f"Loading data: {qa_pairs}")
            # get the local data and add the qa_pairs to that
            data_json_path = os.path.join(cls.name_path, "data.json")
            df: pd.DataFrame = pd.read_json(data_json_path)

            # Add the qa_pairs to the existing data
            if qa_pairs:
                for qa_pair in qa_pairs:
                    df = pd.concat([df, pd.DataFrame([qa_pair])], ignore_index=True)

            required_columns = {"question", "answer"}
            if not required_columns.issubset(df.columns):
                raise ValueError(
                    f"Each QA pair must contain columns: {required_columns}"
                )
            logger.debug("Data loaded successfully.")
            cls.df = df
            return df
        except Exception as e:
            logger.error(f"Error while loading data: {e}")

    def save_dataset(cls, qa_pair: Dict[str, str]) -> pd.DataFrame:
        """
        Saves a dataset from a question-answer pair.

        Parameters:
        - qa_pair (Dict[str, str]): Dictionary with 'question' and 'answer' keys.

        Returns:
        - bool: True if saved successfully, False otherwise.
        """
        try:
            data_json_path = os.path.join(cls.name_path, "data.json")
            with open(data_json_path, "r") as f:
                data: List[Dict[str, Any]] = json.load(f)
                data.append(qa_pair)
            with open(data_json_path, "w") as f:
                json.dump(data, f)

        except Exception as e:
            logger.error(f"Error while saving dataset: {e}")

    def clean_data(cls, cleaner) -> pd.DataFrame:
        try:
            # load the data as df
            # remove whitespaces from the answers json
            # Make sure the json can be loadded into python
            # return the cleaned data

            data_json_path = os.path.join(cls.name_path, "data.json")
            with open(data_json_path, "r") as f:
                data: List[Dict[str, Any]] = json.load(f)
                cleaned_data = []
                for qa_pair in data:
                    cleaned_data.append(cleaner(qa_pair))
            with open(data_json_path, "w") as f:
                json.dump(cleaned_data, f)
        except Exception as e:
            logger.error(f"Error while preparing training data: {e}")

    def prepare_training(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepares the data for training by encoding answers.

        Parameters:
        - df (pd.DataFrame): DataFrame with 'question' and 'answer' columns.

        Returns:
        - pd.DataFrame: DataFrame with encoded labels.
        """
        try:
            df_copy = df.copy()
            # Encode the answers into numerical labels
            df_copy["label"] = cls.label_encoder.fit_transform(df_copy["answer"])
            logger.debug("Answers encoded successfully.")
            return df_copy
        except Exception as e:
            logger.error(f"Error while preparing training data: {e}")

    def build(cls):
        """
        Trains the RandomForestClassifier on the provided dataset.

        Parameters:
        - data_df (pd.DataFrame): DataFrame containing 'question' and 'answer' columns.
        """
        try:
            df = cls.prepare_training(cls.df)
            logger.debug(f'Data prepared for training: {df["label"].nunique()} classes')

            # Initialize and fit the CountVectorizer (or TfidfVectorizer)
            # cls.vectorizer = CountVectorizer(ngram_range=(1, 2), max_features=1000)
            cls.vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=1000)
            # Alternatively, use TfidfVectorizer for better performance
            # cls.vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=1000)

            X = cls.vectorizer.fit_transform(df["question"])
            y = df["label"]
            logger.debug(
                f"Vectorizer fitted. Vocabulary size: {len(cls.vectorizer.vocabulary_)}"
            )

            # Save the vectorizer to disk for future use
            vectorizer_path = os.path.join(cls.name_path, "vectorizer.pkl")
            with open(vectorizer_path, "wb") as f:
                pickle.dump(cls.vectorizer, f)
            logger.debug(f"Vectorizer saved at {vectorizer_path}")

            # Split the data into training and testing sets
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            logger.debug(f"Training set size: {X_train.shape[0]} samples")
            logger.debug(f"Testing set size: {X_test.shape[0]} samples")

            # Initialize and train the RandomForestClassifier
            cls.model = RandomForestClassifier(n_estimators=100, random_state=42)
            cls.model.fit(X_train, y_train)
            logger.debug("RandomForestClassifier trained successfully.")

            # Evaluate the model (optional)
            classes = np.arange(len(cls.label_encoder.classes_))
            y_pred = cls.model.predict(X_test)
            report = classification_report(
                y_test,
                y_pred,
                labels=classes,
                target_names=cls.label_encoder.classes_,
                zero_division=0,
            )
            logger.debug(f"Classification Report:\n{report}")

            # Save the trained model to disk
            model_path = os.path.join(cls.name_path, "model.pkl")
            with open(model_path, "wb") as f:
                pickle.dump(cls.model, f)
            logger.debug(f"Model saved at {model_path}")
        except Exception as e:
            logger.error(f"Error while building the model: {e}")

    def invoke(cls, user_input: str) -> str:
        """
        Predicts the intent of the user input and retrieves the corresponding response.

        Parameters:
        - user_input (str): The input string from the user.

        Returns:
        - str: The chatbot's response.
        """
        try:
            # Load the vectorizer and model if not already loaded
            if cls.vectorizer is None or cls.model is None:
                vectorizer_path = os.path.join(cls.name_path, "vectorizer.pkl")
                model_path = os.path.join(cls.name_path, "model.pkl")
                with open(vectorizer_path, "rb") as f:
                    cls.vectorizer = pickle.load(f)
                with open(model_path, "rb") as f:
                    cls.model = pickle.load(f)
                logger.debug("Vectorizer and model loaded from disk.")

            # Transform the user input using the loaded vectorizer
            X_input = cls.vectorizer.transform([user_input])
            logger.debug(f"User input vectorized: {X_input.toarray()}")

            # Predict the answer label
            predicted_label = cls.model.predict(X_input)[0]
            intent = cls.label_encoder.inverse_transform([predicted_label])[0]
            logger.debug(f"Predicted intent (answer): {intent}")

            # Retrieve the response based on intent
            response = cls.get_response(intent)
            return response
        except Exception as e:
            logger.error(f"Error while invoking the model: {e}")

    def get_response(cls, intent: str) -> str:
        """
        Retrieves a predefined response based on the predicted intent.

        Parameters:
        - intent (str): The predicted intent (answer).

        Returns:
        - str: The chatbot's response.
        """
        return intent  # Since 'intent' now directly refers to the answer


# def chatbot_interaction(chatbot: MLClassifier):
#     """
#     Handles the interaction loop between the user and the chatbot.

#     Parameters:
#     - chatbot (MLClassifier): The trained MLClassifier chatbot instance.
#     """
#     logger.debug("Chatbot is ready! Type 'exit' or 'quit' to stop.")
#     while True:
#         try:
#             user_input = input("You: ").strip()
#         except (EOFError, KeyboardInterrupt):
#             print("\nChatbot: Goodbye! It was nice talking to you.")
#             break

#         if user_input.lower() in ["exit", "quit"]:
#             print("Chatbot: Goodbye! It was nice talking to you.")
#             break
#         response = chatbot.invoke(user_input)
#         print(f"Chatbot: {response}")


# def main():
#     # Example dataset: list of question-answer pairs
#     qa_pairs = [
#         {
#             "question": "What files should I ignore for rippled?",
#             "answer": "[.vscode, .idea, build, dist, node_modules, .git, .DS_Store]",
#         },
#         {
#             "question": "For rippled what files should I ignore?",
#             "answer": "[.vscode, .idea, build, dist, node_modules, .git, .DS_Store]",
#         },
#     ]

#     # Create a DataFrame from the dataset
#     df = pd.DataFrame(qa_pairs)

#     # Initialize the MLClassifier chatbot
#     ai_chatbot = MLClassifier(
#         storage_type="local",
#         id="chatbot_01",
#         dir="chatbot_data",
#         name="qa_bot",
#         version="v1",
#         features=["question"],  # Feature used for classification
#     )

#     # Load the dataset
#     loaded_data = ai_chatbot.load_data(qa_pairs)

#     # Train the model
#     ai_chatbot.build(loaded_data)

#     # Start the chatbot interaction
#     chatbot_interaction(ai_chatbot)


# # if __name__ == "__main__":
# #     main()
