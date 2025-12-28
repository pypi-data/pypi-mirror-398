"""Submission class for JotForm API interactions."""

# pylint: disable=C0115, C0116, C0103
from abc import ABC
from datetime import datetime
from typing import Union, Dict, Optional, List
import requests
from .types import AnswerObject, AnswerValue, Submission as SubmissionType


class JotFormSubmission(ABC):
    # TODO seperate this class into another file
    """Base class for JotFormSubmission.
    Takes a submission object and creates a submission object from it.

    Args:
        ABC (_type_): parent class
    """

    id: str
    form_id: str
    ip: str
    api_key: str
    created_at: str
    status: str
    new: bool
    flag: bool
    notes: str
    updated_at: str
    answers: List[AnswerObject]
    answers_arr: List[AnswerObject]
    emails: List[str]

    def __init__(self, submission_object: SubmissionType, api_key: str):
        self.api_key = api_key
        self.id = submission_object.get("id", "")
        self.form_id = submission_object.get("form_id", "")
        self.ip = submission_object.get("ip", "")
        self.created_at = submission_object.get("created_at", "")
        self.status = submission_object.get("status", "")
        self.new = submission_object.get("new", False)
        self.flag = submission_object.get("flag", False)
        self.notes = submission_object.get("notes", "")
        self.updated_at = submission_object.get("updated_at", "")
        self.answers = submission_object.get("answers", {})
        self._clear_answers()
        self.answers_arr = self.set_answers(self.answers)
        self.emails = self.get_emails()

    def set_answers(self, answers: AnswerObject) -> List[Optional[AnswerObject]]:
        """## This function sets the answers array

        Args:
            answers (AnswerObject): _description_

        Returns:
            List[Optional[AnswerObject]]: _description_
        """
        answers_arr: List[AnswerObject] = []
        for key, value in answers.items():
            name = None
            if "name" in value:
                name = value["name"]
            answer = None
            if "answer" in value:
                answer = value["answer"]
            _type = None
            if "type" in value:
                _type = value["type"]
            text = None
            if "text" in value:
                text = value["text"]
            file = None
            if "file" in value:
                file = value["file"]
            answers_arr.append(
                {
                    "key": key,
                    "name": name,
                    "answer": answer,
                    "type": _type,
                    "text": text,
                    "file": file,
                }
            )
        return answers_arr

    def _clear_answers(self) -> None:
        """Process of getting rid of unnecessary keys in the answers dictionary."""
        for _, answer in self.answers.items():
            if "maxValue" in answer:
                del answer["maxValue"]
            if "order" in answer:
                del answer["order"]
            if "selectedField" in answer:
                del answer["selectedField"]
            if "cfname" in answer:
                del answer["cfname"]
            if "static" in answer:
                del answer["static"]
            if "type" in answer and answer["type"] != "control_email":
                del answer["type"]
            if "sublabels" in answer:
                del answer["sublabels"]
            if "timeFormat" in answer:
                del answer["timeFormat"]

    def set_answer(self, answer_key: str, answer_value: AnswerObject) -> None:
        """## sets answer value for the given answer id

        Args:
            answer_key (str): order integer of the answer
            answer_value (AnswerObject): value you want to set for the answer
        """

        for i, answer in enumerate(self.answers_arr):
            if answer["key"] == answer_key:
                self.answers_arr[i]["answer"] = answer_value
        self.answers[answer_key]["answer"] = answer_value
        self.update_submission(self.id, answer_key, answer_value, self.api_key)

    def set_answer_by_text(self, answer_text: str, answer_value: AnswerObject) -> None:
        """## sets answer value for the given answer text

        Args:
            answer_text (str): answer_text of the answer
            answer_value (AnswerObject): value you want to set for the answer
        """
        for i, answer in enumerate(self.answers_arr):
            if answer.get("text") == answer_text:
                self.answers_arr[i]["answer"] = answer_value
        self.get_answer_by_text(answer_text)["answer"] = answer_value
        answer_key = self.get_answer_by_text(answer_text).get("key")
        self.update_submission(self.id, answer_key, answer_value, self.api_key)

    def set_answer_by_name(self, answer_name: str, answer_value: AnswerObject) -> None:
        """## sets answer value for the given unique answer name

        Args:
            answer_name (str): answer_name of the answer
            answer_value (AnswerObject): value you want to set for the answer
        """
        for i, answer in enumerate(self.answers_arr):
            if answer["name"] == answer_name:
                self.answers_arr[i]["answer"] = answer_value
        self.get_answer_by_name(answer_name)["answer"] = answer_value
        answer_key = self.get_answer_by_name(answer_name).get("key")
        self.update_submission(self.id, answer_key, answer_value, self.api_key)

    def set_answer_by_key(self, answer_key: str, answer_value: AnswerObject) -> None:
        """## sets answer value for the given unique answer key

        Args:
            answer_key (str): answer_key of the answer
            answer_value (AnswerObject): value you want to set for the answer
        """
        for i, answer in enumerate(self.answers_arr):
            if answer["key"] == answer_key:
                self.answers_arr[i]["answer"] = answer_value
        self.get_answer_by_key(answer_key)["answer"] = answer_value
        self.update_submission(self.id, answer_key, answer_value, self.api_key)

    @classmethod
    def update_submission(
        cls, submission_id: str, key: str, value: str, api_key: str
    ) -> None:
        """
        Triggers an update for a specific submission in JotForm.

        This method sends a POST request to the JotForm API to update a specific field
        in a submission with a given value.

        Args:
            submission_id (str): The ID of the submission to be updated.
            key (str): The key of the field to be updated.
            value (str): The new value to be set for the specified field.
            api_key (str): The API key to authenticate the request.

        Raises:
            ConnectionError: If the request to the JotForm API fails due to a connection error.

        Example:
            self.trigger_submission_update("1234567890", "status", "active", "your_api_key")
        """
        query = f"submission[{key}]={value}"
        url = f"https://api.jotform.com/submission/{submission_id}?apiKey={api_key}&{query}"
        try:
            requests.post(url, timeout=45)
        except ConnectionError:
            print(f"cannot trigger for {submission_id}")

    def get_answers(self) -> List[AnswerObject]:
        """## This function gets the answers array

        Returns:
            list: answers array
        """
        return self.answers_arr

    def get_answer_by_text(self, text: str) -> AnswerObject:
        """## This function gets the answer by text
         Sensetive to the text, if the text is not exactly the same, it will return None

        Args:
            - `text (str)`: text element to search for

        Returns:
            - `Dict`: jotform return object
            {
                "key": "key",
                "name": "name",
                "answer": "answer",
                "type": "type",
                "text": "text",
                "file": "file"
            }
        """
        for answer in self.answers_arr:
            if answer.get("text") and answer.get("text").upper() == text.upper():
                _answer = answer.copy()
                if not answer.get("answer"):
                    _answer["answer"] = None
                answer_value = _answer.get("answer")
                if isinstance(answer_value, list) and len(answer_value) == 1:
                    _answer["answer"] = answer_value[0]
                return _answer
        raise ValueError(f"Answer with text '{text}' not found")

    def get_answer_by_name(self, name: str) -> AnswerObject:
        for answer in self.answers_arr:
            if answer["name"] and answer["name"] == name:
                _answer = answer.copy()
                if not answer.get("answer"):
                    _answer["answer"] = None
                answer_value = _answer.get("answer")
                if isinstance(answer_value, list) and len(answer_value) == 1:
                    _answer["answer"] = answer_value[0]
                return _answer
        raise ValueError(f"Answer with name '{name}' not found")

    def get_answer_by_key(self, key: Union[str, int]) -> AnswerObject:
        for answer in self.answers_arr:
            if answer["key"] and answer["key"] == str(key):
                _answer = answer.copy()
                if not answer.get("answer"):
                    _answer["answer"] = None
                answer_value = _answer.get("answer")
                if isinstance(answer_value, list) and len(answer_value) == 1:
                    _answer["answer"] = answer_value[0]
                return _answer
        raise ValueError(f"Answer with key '{key}' not found")

    def __delitem__(self, key: str):
        """Delete an answer using del operator.

        Args:
            key: The answer key to delete

        Example:
            del submission_instance[key]
        """
        if key not in self.answers:
            raise KeyError(f"Answer with key '{key}' not found")

        # Remove from answers dict
        del self.answers[key]

        # Remove from answers_arr
        self.answers_arr = [
            answer for answer in self.answers_arr if answer["key"] != key
        ]

    def get_emails(self) -> List[Optional[str]]:
        """## This function gets the emails from the answers array

        Returns:
            List[Optional[str]]: list of emails (or None for missing answers)
        """
        emails: List[Optional[str]] = []
        for answer in self.answers_arr:
            if "type" not in answer:
                continue
            if answer["type"] == "control_email":
                # use .get to avoid KeyError and allow None values
                emails.append(answer.get("answer"))
        return emails

    def get_day_from_date(self, date: Union[str, Dict[str, str], datetime]) -> int:
        """Given parameter is expected to be YYYY-MM-DD hh:mm:ss or a dict with 'answer'/'datetime' or a datetime.

        Returns the number of days between now and the given date.
        """
        if isinstance(date, dict):
            date = date.get("answer") or date.get("datetime")

        if isinstance(date, datetime):
            delta = datetime.now() - date
            return delta.days

        if isinstance(date, str):
            try:
                parsed = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                return (datetime.now() - parsed).days
            except ValueError:
                raise ValueError(
                    "Invalid date string format, expected '%Y-%m-%d %H:%M:%S'"
                )

        raise ValueError("Invalid date format")

    def get_store_number_from_store(self, store: str) -> str:
        """If store is in the format of 'store | store_number', return store_number."""
        return store.split(" | ")[0]

    def to_dict(self) -> Dict[str, Union[str, int, bool, List[Optional[str]]]]:
        """## This function returns the submission object as a dictionary,
        recomendation use case is to inherit this function in your own to_dict call

        Returns:
            Dict: _description_
        """
        return {
            "id": self.id,
            "form_id": self.form_id,
            "created_at": self.get_day_from_date(self.created_at),
            "ip": self.ip,
            "new": self.new,
            "flag": self.flag,
            "notes": self.notes,
            "updated_at": self.updated_at,
            "emails": self.get_emails(),
        }

    def turn_into_american_datetime_format(
        self,
        date: Union[str, Dict[str, str], datetime],
        cur_frmt: str = "%Y-%m-%d %H:%M:%S",
        end_frmt: str = "%m/%d/%Y %I:%M %p",
    ) -> str:
        if isinstance(date, dict):
            date = date.get("answer") or date.get("datetime")

        if isinstance(date, str):
            date = datetime.strptime(date, cur_frmt)

        if isinstance(date, datetime):
            return date.strftime(end_frmt)

        raise ValueError("Invalid date format")

    def text_to_html(self, text: Optional[str]) -> Optional[str]:
        """Converts plain text to HTML format."""
        if not text:
            return None
        text = text.replace("\r\n", "<br>")  # Convert Windows-style line breaks
        text = text.replace("\n", "<br>")  # Convert Unix-style line breaks
        text = text.replace("\r", "<br>")  # Convert Mac-style line breaks
        paragraphs = text.split("<br><br>")  # Split the text into paragraphs

        html = ""
        for paragraph in paragraphs:
            html += "<p>" + paragraph + "</p>"
        return html

    def split_domain_from_email(self, email: str):
        """if @ in email, split and return the first part of the string

        Args:
            email (str): string with @ in it

        Returns:
            _type_: first half of an email address.
            e.g: 'test' from 'test@test.com'
        """
        if not email:
            return None
        elif "@" in email:
            return email.split("@")[0]
        else:
            return email

    def get_value(self, obj: AnswerObject) -> Optional[AnswerValue]:
        """## This function gets the value from the object
            When you call this it wont raise an error which makes it the safer version of ["answer"]
            Example:
            self.get_value(self.get_answer_by_text("CASE"))
            self.get_answer_by_text("CASE")["answer"]

        Args:
            obj (AnswerObject): _description_

        Returns:
            Optional[Union[AnswerValue, AnswerObject]]: _description_
        """
        if isinstance(obj, str):
            return obj.strip()
        elif isinstance(obj, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
            if "answer" in obj:
                answer: AnswerValue = obj["answer"]
                if isinstance(answer, list):
                    return answer[0]
                return answer
            elif len(obj) > 1:
                return obj
            elif len(obj) == 1:
                return next(iter(obj.values()))
        else:
            return None

    def tide_answer_for_list(self, answer: AnswerObject) -> str:
        """## This function converts the answer to a string, gives commas for each answer `,`
        ### Output is like:
            * Answer 1, Answer 2, Answer 3
        Args:
            answer (AnswerObject): _description_

        Returns:
            str: _description_
        """
        string = ""
        if isinstance(answer, list):
            for i, value in enumerate(answer):
                value = str(value).title()
                if i == 0:
                    string += f"{value}"
                else:
                    string += f", {value}"
        else:  # answer is a dict
            for i, value in enumerate(answer.items()):
                value = str(value[1]).title()
                if i == 0:
                    string += f"{value}"
                else:
                    string += f", {value}"
        return string

    def answer_for_html(self, answer: AnswerObject) -> str:
        """## This function converts the answer to HTML format, gives breaks for each answer `<br>`
        ### Output is like:
            * Answer 1
            * Answer 2
            * Answer 3

        Args:
            answer (str or dict): answer to be converted to HTML

        Returns:
            str: HTML formatted string
        """
        html = ""
        if isinstance(answer, list):
            for i, value in enumerate(answer):
                value = str(value).title()
                if i == 0:
                    html += f"*{value}"
                else:
                    html += f"<br>*{value}"
        elif isinstance(answer, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
            for i, value in enumerate(answer.items()):
                value = str(value[1]).title()
                if i == 0:
                    html += f"*{value}"
                else:
                    html += f"<br>*{value}"
        elif isinstance(answer, str):  # pyright: ignore[reportUnnecessaryIsInstance]
            html = f"*{answer.title()}"
        elif answer is None:
            html = "*None"
        else:
            html = f"*{answer}"
        return html

    def make_array(self, answer: AnswerObject) -> List[AnswerValue]:
        if not answer:
            return []
        elif isinstance(answer, int):
            return [answer]

        if "answer" in answer:
            answer = answer["answer"]

        if isinstance(answer, list):
            return answer
        elif isinstance(answer, str):
            if answer.strip() == "":
                return []
            elif "," in answer:
                return [x.strip() for x in answer.split(",")]
            else:
                return [answer]
        else:
            return []
