"""## [JOTFORM API DOCS](https://www.api.jotform.com)"""

# pylint: disable=C0115, C0116, C0103
import json
from abc import ABC
from datetime import datetime
from typing import Union, Dict, Optional, List, Any, Set
from urllib.parse import quote
from time import sleep
import requests
from requests.exceptions import RequestException
from json.decoder import JSONDecodeError
from .utils import fix_query_key
from .jotFormSubmission import JotFormSubmission
from .types import AnswerObject, AnswersDict, FormObject, JotformFormAPIResponse


class JotForm(ABC):
    """JotForm API client to fetch and manage form submissions.
    Args:
        api_key (str): JotForm API key used for authentication.
        form_id (str): ID of the JotForm form.
        timeout (int): Request timeout in seconds (default: 45).

    This class provides methods to list, create, update, and delete submissions,
    and to query submissions by various criteria.
    """

    debug: bool = False
    update_timestamp: float
    api_key: str
    form_id: str
    url: str
    submission_ids: Set[str]
    submission_data: Dict[str, JotFormSubmission]
    updating_process: bool
    submission_count: int
    timeout: int

    def __init__(self, api_key: str, form_id: str, timeout: int = 45):
        self.update_timestamp = datetime.now().timestamp()
        self.api_key = api_key
        self.form_id = form_id
        self.url = (
            "https://api.jotform.com/form/"
            + form_id
            + "/submissions?limit=1000&apiKey="
            + api_key
        )
        self.set_url_param("offset", "0")
        self.submission_ids = set()
        self.submission_data = {}
        self.updating_process = False
        self.submission_count = 0
        self.timeout = timeout
        self.update()

    @classmethod
    def build_url(cls, form_id: str, api_key: str) -> str:
        return (
            "https://api.jotform.com/form/"
            + form_id
            + "/submissions?limit=1000&apiKey="
            + api_key
        )

    def _print(self, text: str) -> None:
        if self.debug:
            print(text)

    @classmethod
    def _set_get_submission_data(
        cls,
        submissions: List[Dict[str, Any]],
        api_key: str,
        include_deleted: bool = False,
    ) -> Dict[str, JotFormSubmission]:
        """Sets and gets submission data.

        Args:
            submissions (List[Dict[str, Any]]): List of submissions.
            api_key (str): API key for authentication.
            include_deleted (bool, optional): Whether to include deleted submissions. Defaults to False.

        Returns:
            Dict: Dictionary of submission data.
        """
        submissions_dict: Dict[str, JotFormSubmission] = {}
        for sub in submissions:
            if sub["status"] == "DELETED" and not include_deleted:
                continue
            submissions_dict[sub["id"]] = JotFormSubmission(sub, api_key)
        return submissions_dict

    def get_submission_ids(self) -> Set[str]:
        return self.submission_ids

    def _set_submission_ids(self) -> None:
        """This function sets the submission memory. It is used for easier for loop for submissions.
        It is called in the constructor, and time to time in other functions"""
        self.submission_ids = set()
        for _, value in self.submission_data.copy().items():
            self.submission_ids.add(value.id)

    def _set_submission_count(self) -> None:
        self.submission_count = len(self.submission_ids)

    def get_submission_data(self) -> Dict[str, JotFormSubmission]:
        self.update()
        return self.submission_data

    def get_submission_count(self) -> int:
        return self.submission_count

    def get_submission_answers(
        self, submission_id: Union[int, str]
    ) -> List[AnswerObject]:
        """## Returns the answers of the submission by given submission id

        Args:
            submission_id (int or str):

        Returns:
            Dict: answers of the submission
        """
        self.update()
        return self.submission_data[str(submission_id)].answers

    def get_submission_by_request(
        self, submission_id: Union[str, int]
    ) -> Optional[object]:
        """## This function gets the submission by request

        Args:
            submission_id (_type_): _description_

        Returns:
            Optional[object]: _description_
        """
        url = (
            f"https://api.jotform.com/submission/{submission_id}?apiKey={self.api_key}"
        )
        response = requests.get(url, timeout=self.timeout)
        if response.status_code == 200:
            response = response.json()
            return response["content"]
        return None

    def get_submission(self, submission_id: Union[int, str]) -> JotFormSubmission:
        return self.submission_data[str(submission_id)]

    def get_submissions(self) -> Dict[str, JotFormSubmission]:
        return self.get_submission_data()

    def get_submission_by_text(self, text: str, text_answer: str) -> Optional[object]:
        """## This function gets the submission by text and answer's text
            {
                "key": 1,
                "name": "userName",
                "answer": "John Doe",
                "type": "control_textbox",
                "text": "What is Your User Name",
            }
        Args:
            text (str): _description_
            text_answer (str): _description_

        Returns:
            Optional[object]: submission object if successful, None if not
        """
        for _, submission_object in self.submission_data.copy().items():
            answer: AnswerObject = submission_object.get_answer_by_text(text)
            if answer == text_answer:
                return submission_object
        return None

    def get_submission_by_name(self, name: str, name_answer: str) -> Optional[object]:
        """## This function gets the submission by name and answer's name
            {
                "key": 1,
                "name": "userName",
                "answer": "John Doe",
                "type": "control_textbox",
                "text": "What is Your User Name",
            }
        Args:
            name (str): _description_
            name_answer (str): _description_

        Returns:
            Optional[object]: submission object if successful, None if not
        """
        for _, submission_object in self.submission_data.copy().items():
            answer: AnswerObject = submission_object.get_answer_by_name(name)
            if answer == name_answer:
                return submission_object
        return None

    def get_submission_by_key(
        self, key: Union[str, int], key_answer: str
    ) -> Optional[object]:
        """## This function gets the submission by key and answer's key
            {
                "key": 1,
                "name": "userName",
                "answer": "John Doe",
                "type": "control_textbox",
                "text": "What is Your User Name",
            }
        Args:
            key (Union[str, int]): _description_
            key_answer (str): _description_

        Returns:
            Optional[object]: submission object if successful, None if not
        """
        for _, submission_object in self.submission_data.copy().items():
            answer = submission_object.get_answer_by_key(key)
            if answer == key_answer:
                return submission_object
        return None

    def get_answer_by_text(
        self, submission_id: Union[int, str], text: str
    ) -> AnswerObject:
        try:
            return self.get_submission(submission_id).get_answer_by_text(text)
        except KeyError:
            self.update()
            return self.get_submission(submission_id).get_answer_by_text(text)

    def get_answer_by_name(
        self, submission_id: Union[int, str], name: str
    ) -> AnswerObject:
        try:
            return self.get_submission(submission_id).get_answer_by_name(name)
        except KeyError:
            self.update()
            return self.get_submission(submission_id).get_answer_by_name(name)

    def get_answer_by_key(
        self, submission_id: Union[int, str], key: str
    ) -> AnswerObject:
        try:
            return self.get_submission(submission_id).get_answer_by_key(key)
        except KeyError:
            self.update()
            return self.get_submission(submission_id).get_answer_by_key(key)

    def get_answer_by_id(
        self, submission_id: Union[int, str], key: str
    ) -> AnswerObject:
        return self.get_answer_by_key(submission_id, key)

    def get_submission_answers_by_question(
        self, submission_id: Union[int, str]
    ) -> AnswersDict:
        return self.get_submission_answers_by_question_id(submission_id)

    def get_submission_answers_by_question_id(
        self, submission_id: Union[int, str]
    ) -> AnswersDict:
        self.update()
        submission_answers = self.get_submission_answers(submission_id)
        submission_answers_by_question_id: AnswersDict = {}
        for answer in submission_answers:
            if "id" in answer and "answer" in answer:
                submission_answers_by_question_id[answer["id"]] = answer["answer"]
        return submission_answers_by_question_id

    def get_list_of_questions(self):
        """## jotform endpoint of form/{id}/questions

        ### Returns:
            - `object` or 'bool': questions list if successful, false if not
        """
        url = f"https://api.jotform.com/form/{self.form_id}/questions?apiKey={self.api_key}"
        response = requests.get(url, timeout=self.timeout)
        if response.status_code == 200:
            response = response.json()
            return response["content"]
        return None

    def __delitem__(self, submission_id: Union[int, str]):
        """Delete a submission using del operator.

        Args:
            submission_id: The submission ID to delete

        Example:
            del jotform_instance[submission_id]
        """
        if str(submission_id) not in self.submission_data:
            raise KeyError(f"Submission {submission_id} not found")

        url = (
            f"https://api.jotform.com/submission/{submission_id}?apiKey={self.api_key}"
        )
        response = requests.delete(url, timeout=self.timeout)
        if response.status_code == 200:
            del self.submission_data[submission_id]
            self.submission_ids.discard(submission_id)
            self._set_submission_count()
        else:
            raise RuntimeError(f"Failed to delete submission {submission_id}")

    def delete_submission(self, submission_id: Union[int, str]) -> bool:
        url = (
            f"https://api.jotform.com/submission/{submission_id}?apiKey={self.api_key}"
        )
        response = requests.delete(url, timeout=self.timeout)
        if response.status_code == 200:
            del self.submission_data[submission_id]
            return True
        return False

    def create_submission(self, submission: Dict[str, Any]) -> Union[bool, str]:
        """## This function creates a submission in Jotform
        then sets the new submission to the submission data.

        ### Args:
            - `submission (pseudo sumbission dictionary)`:
               {
                    "submission[1]": "value",
                    "submission[2]": "value",
                    ...
               }

        ### Returns:
            - `bool` or 'string': new created submission's id if successful, false if not
        """
        url = f"https://api.jotform.com/form/{self.form_id}/submissions?apiKey={self.api_key}"
        response = requests.post(url, data=submission, timeout=self.timeout)
        if response.status_code == 200:
            response = response.json()
            _id = response["content"]["submissionID"]
            submission_data = self.get_submission_by_request(_id)
            if submission_data:
                self.set_new_submission(submission_data)
                return _id
        return False

    def create_submission_using_another(
        self, submission_data: Dict[str, Any], submission_to_copy: JotFormSubmission
    ) -> Union[bool, str]:
        """## This function creates a submission in Jotform
        then sets the new submission to the submission data.

        ### Args:
            - `submission_data (sumbission dictionary)`:
            contains name value pairs of the submission
            e.g:
               {
                    "data": "value",
                    "data2": "value",
                    ...
               }
            - submission_to_copy (JotFormSubmission): submission object to copy

        ### Returns:
            - `bool`: true if successful, false if not
        """
        data: Dict[str, Any] = {}
        questions = self.get_list_of_questions()
        if not questions:
            return False
        for q in questions:
            name = questions[q]["name"]
            if name in submission_data:
                data[f"submission[{q}]"] = submission_data[name]
            else:
                answer_obj = submission_to_copy.get_answer_by_name(name)
                answer = (
                    answer_obj["answer"]
                    if "answer" in answer_obj
                    else None
                )
                if answer:
                    data[f"submission[{q}]"] = answer
        return self.create_submission(data)

    def update_submission_answers_batch(
        self, submission_id: Union[int, str], answers: AnswersDict
    ) -> bool:
        """## This function updates multiple answers of the submission in a single batch request

        ### Args:
            - `submission_id (Union[int, str])`: Submission ID
            - `answers (AnswersDict)`: Dictionary of field_id to answer

        ### Returns:
            - `bool`: True if successful, False if not
        """
        data: Dict[str, Any] = {}
        for answer_key, answer_value in answers.items():
            if isinstance(answer_value, list):
                data[f"submission[{answer_key}][]"] = answer_value
            else:
                data[f"submission[{answer_key}]"] = answer_value
        url = f"https://api.jotform.com/submission/{submission_id}"
        response = requests.post(
            url,
            params={"apiKey": self.api_key},
            data=data,
            timeout=self.timeout,
        )
        if response.status_code == 200:
            for answer_key, answer_value in answers.items():
                self.submission_data[str(submission_id)].set_answer(
                    answer_key, answer_value
                )
            return True
        return False

    def update_submission_answer(
        self, submission_id: Union[int, str], field_id: str, answer: AnswerObject
    ) -> bool:
        """## This function updates the answer of the submission

        ### Args:
            - `submission_id (Union[int, str])`: _description_
            - `field_id (str)`: _description_
            - `answer (Union[int, str])`: _description_

        ### Returns:
            - `bool`: True if successful, False if not
        """
        if isinstance(answer, list):
            data = {f"submission[{field_id}][]": answer}
            response = requests.post(
                f"https://api.jotform.com/submission/{submission_id}",
                params={"apiKey": self.api_key},
                data=data,
                timeout=self.timeout,
            )
        else:
            query = f"submission[{field_id}]={answer}"
            url = f"https://api.jotform.com/submission/{submission_id}"
            url += f"?apiKey={self.api_key}&{query}"
            response = requests.post(url, timeout=self.timeout)
        if response.status_code == 200:
            self.submission_data[str(submission_id)].set_answer(field_id, answer)
            return True
        return False

    def set_url_param(self, key: Union[str, int], value: Union[str, int]) -> None:
        """Sets the URL parameter.

        Available keys:
            - `apiKey`: Your JotForm API key for authentication.\n
            - `limit`: Specifies the maximum number of results to return.\n
            - `offset`: Specifies the number of results to skip before starting to return results.\n
            - `orderby`: Determines the field by which to sort the results.\n
            - `filter`: Applies a filter to the results based on specified criteria.\n
            - `search`: Searches for a specific term within the results.\n
            - `sort`: Specifies the sort order of the results (e.g., ascending or descending).\n
            - `fields`: Specifies which fields to include in the response.\n
            - `id`: Filters results by a specific ID.\n
            - `created_at`: Filters results based on their creation date.\n
            - `updated_at`: Filters results based on their last updated date.

        Args:
            key (str): The key to set in the URL.
            value (str): The value to set for the specified key.
        """
        value = str(value)
        key_str = str(key)
        base_url, params = self.url.split("?")
        if key_str in params:
            params = params.split("&")
            for i, param in enumerate(params):
                if key_str in param:
                    params[i] = key_str + "=" + value
            self.url = base_url + "?" + "&".join(params)
        else:
            self.url += "&" + key_str + "=" + value

    def sort_submission_data_by_id(self) -> None:
        """## Sorts the submission data by id
        No need to sort since it is already sorted by the API
        unless orderby is changed in the url for descending order
        """
        sorted_tuples = sorted(
            self.submission_data.copy().items(), key=lambda x: x[1].id, reverse=True
        )
        sorted_dict = {k: v for k, v in sorted_tuples}
        self.submission_data = sorted_dict

    def get_missing_submission_id(self) -> Optional[int]:
        """## This function gets the missing submission id

        Returns:
            Optional[int]: return the missing submission id if there is any
        """
        all_submission_ids = set(int(sid) for sid in self.get_submission_ids())
        expected_submission_ids = set(range(1, self.submission_count + 1))
        missing_ids = expected_submission_ids - all_submission_ids
        if missing_ids:
            return missing_ids.pop()

    def _fetch_new_submissions(
        self, count: int, attempt: int = 0, max_attempts: int = 5
    ) -> bool:
        """## It is already newest to oldest so we can request one query, and it should be enough

        Args:
            count (_type_): Fresh count of the submissions
            attempt (_type_, optional): Current number of attempts. Defaults to 0.
            max_attempts (_type_, optional): Maximum number of attempts. Defaults to 5.

        Returns:
            bool: True if updates, False if not
        """
        count = count - self.submission_count
        if count <= 0:
            return False
        limit = 1000 if count > 1000 else count
        self.set_url_param("limit", limit)
        self.set_url_param("orderby", "id")
        try:
            response = requests.get(self.url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            self.submission_data.update(
                self._set_get_submission_data(data["content"], self.api_key)
            )
            if len(data["content"]) < limit:
                self.set_global_data()
                return True
            elif limit >= 1000:
                self.set_url_param("offset", data["resultSet"]["offset"] + limit)
                sleep(0.33)
                return self._fetch_new_submissions(count - limit, attempt)
            self.set_global_data()
            return True

        except requests.exceptions.HTTPError as http_err:
            if http_err.response is not None and http_err.response.status_code == 429:
                self._print(
                    f"Request failed: {http_err} (429 Too Many Requests). Retrying with backoff..."
                )
                if attempt < max_attempts:
                    sleep_time = 2**attempt
                    sleep(sleep_time)
                    return self._fetch_new_submissions(
                        count + self.submission_count, attempt + 1
                    )
            self._print(f"Request failed: {http_err}")
        except (RequestException, JSONDecodeError) as e:
            self._print(f"Request failed: {e}")
            if attempt < max_attempts:
                sleep(0.666)
                return self._fetch_new_submissions(
                    count + self.submission_count, attempt + 1
                )

        except KeyError as e:
            self._print(f"KeyError: {e}")

        return False

    def _fetch_updated_submissions(
        self, attempt: int = 0, max_attempts: int = 5
    ) -> bool:
        """## This function gets the last updated data from the Jotform API.
            Aim of this function is to get last 1000 submissions sorted by updated_at.
            So that network traffic is less and we can get the most recent data.

        Args:
            attempt (_type_, optional): Current number of attempts. Defaults to 0.
            max_attempts (_type_, optional): Maximum number of attempts. Defaults to 5.

        Returns:
            bool: True if updates, False if not
        """
        self.set_url_param("limit", "1000")
        self.set_url_param("orderby", "updated_at")
        self.set_url_param("offset", "0")
        try:
            response = requests.get(self.url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            self.submission_data.update(
                self._set_get_submission_data(data["content"], self.api_key)
            )
            self.set_global_data()
            return True

        except (RequestException, JSONDecodeError) as e:
            self._print(f"Request failed: {e}")
            if attempt < max_attempts:
                sleep(0.666)
                return self._fetch_updated_submissions(attempt + 1)

        except KeyError as e:
            self._print(f"KeyError: {e}")

        return False

    def set_global_data(self) -> None:
        self._set_submission_ids()
        self._set_submission_count()
        self._reset_url_params()

    def request_submission_by_case_id(self, case_id: str) -> Optional[object]:
        """
        Requests the submission by case id
        this function is used when the submission is not in the submission data
        """
        query = quote(f"""{{"q221:matches:answer":"{case_id}"}}""")
        url = f"https://api.jotform.com/form/{self.form_id}/submissions"
        url += f"?apiKey={self.api_key}&filter={query}"
        response = requests.get(url, timeout=self.timeout)
        if response.status_code != 200:
            return None
        _json = response.json()
        return _json

    def set_new_submission(self, submission: Dict[str, Any]) -> None:
        self.submission_data.update(
            self._set_get_submission_data([submission], self.api_key)
        )
        self.set_global_data()

    def get_form(self) -> Optional[JotformFormAPIResponse]:
        """
        Gets form data directly from Jotform so there is no data diffirence on this function.
        It is slow since we are requesting data from Jotform.

        Returns:
            Optional[JotformFormAPIResponse]: object if successful, None if not
        """
        url = f"https://api.jotform.com/form/{self.form_id}?apiKey={self.api_key}"
        response = requests.get(url, timeout=self.timeout)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def _fetch_submissions_count(self) -> int:
        form = self.get_form()
        if form:
            content: FormObject = form.get("content", {})
            return int(content.get("count", 0))
        return 1

    def update(self, force: bool = False) -> bool:
        """## This function updates the data from the Jotform API
            It will look for a change in the submission count,
            updates the data accordingly unless force is True

        Args:
            force (bool, optional): If True, it will update all the submissions. Defaults to False.

        Returns:
            bool: True if updates, False if not
        """
        if not self.updating_process:
            self.updating_process = True
            now = datetime.now().timestamp()
            its_been = now - self.update_timestamp
            if its_been > 300 or force:
                # been more than 5 minutes so only pull the 100 posibly recently updated submissions
                self.update_timestamp = now
                self._fetch_updated_submissions()
            else:
                count = self._fetch_submissions_count()
                if count != self.submission_count:
                    # only pull the new submissions if there is a change in the submission count
                    self._fetch_new_submissions(count)
                else:
                    self.updating_process = False
                    self._print("[INFO] No new submissions.")
                    return False
            self._reset_url_params()
            self._print(
                f"[INFO] Update process is completed.\
                Last update was {int(its_been/60)} minutes ago."
            )
            self.updating_process = False
            return True
        self._reset_url_params()
        self._print("[INFO] Update process is already running.")
        return False

    def _reset_url_params(self) -> None:
        self.set_url_param("offset", "0")
        self.set_url_param("limit", "1000")
        self.set_url_param("orderby", "id")

    def get_user_data_by_email(self, email: str) -> Optional[List[JotFormSubmission]]:
        """
        ## This function gets the user data by email address

        Returns:
            Optional[List[JotFormSubmission]]: List of submissions for the given email, or None if email is not provided.
        """
        if not email:
            return None
        email = email.lower()
        self.update()
        submissions: List[JotFormSubmission] = []
        for _, submission in self.submission_data.copy().items():
            submission_object = self.get_submission(submission.id)
            email_objects = [i.lower() for i in submission_object.emails if i]
            if email in email_objects:
                submissions.append(submission_object)
        return submissions

    @classmethod
    def get_submission_data_by_query(
        cls, filter_param: Union[Dict[str, Any], str], api_key: str, form_id: str
    ) -> Dict[str, JotFormSubmission]:
        """
        Query submissions using JotForm API filter param as JSON string or plain string.
        Accepts either a Dict (converted to JSON string) or a pre-formatted string.
        If Dict: checks key format, adds 'q' if missing, logs about it, or throws error if only a number.
        Example: '{"q3:matches":"Will VanSaders"}' or {"q3:matches": "Will VanSaders"}
        """

        if not filter_param:
            raise ValueError("filter_param must be a non-empty dict or string")

        if isinstance(filter_param, dict):
            new_filter = {}
            for k, v in filter_param.items():
                fixed_key = fix_query_key(k)
                new_filter[fixed_key] = v
            filter_str = json.dumps(new_filter)
        elif isinstance(filter_param, int):
            raise ValueError("filter_param cannot be only a number")
        else:
            try:
                filter_dict = json.loads(filter_param)
                new_filter = {}
                for k, v in filter_dict.items():
                    fixed_key = fix_query_key(k)
                    new_filter[fixed_key] = v
                filter_str = json.dumps(new_filter)
            except Exception:
                # If not JSON, just use as-is
                filter_str = filter_param

        params = {"filter": filter_str}
        response = requests.get(
            cls.build_url(form_id, api_key), params=params, timeout=45
        )
        if response.status_code == 200:
            submissions = response.json().get("content", [])
            return cls._set_get_submission_data(submissions, api_key)
        else:
            print(f"JotForm API error: {response.status_code} - {response.text}")
        return {}
