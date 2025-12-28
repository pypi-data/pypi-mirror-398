import unittest
from unittest.mock import Mock, patch, MagicMock
from crossmark_jotform_api.jotForm import JotForm, JotFormSubmission


class TestJotFormUnit(unittest.TestCase):
    """Unit tests for JotForm that don't require real API calls"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.api_key = "test_api_key"
        self.form_id = "123456"

    def test_build_url(self):
        """Test URL building functionality"""
        expected_url = f"https://api.jotform.com/form/{self.form_id}/submissions?limit=1000&apiKey={self.api_key}"
        result = JotForm.build_url(self.form_id, self.api_key)
        self.assertEqual(result, expected_url)

    @patch("crossmark_jotform_api.jotForm.requests.get")
    def test_get_form_success(self, mock_get):
        """Test successful form retrieval"""
        # Mock the response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "responseCode": 200,
            "content": {"id": self.form_id, "title": "Test Form"},
        }
        mock_get.return_value = mock_response

        # Create JotForm instance with mocked update
        with patch.object(JotForm, "update"):
            jotform = JotForm(self.api_key, self.form_id)
            result = jotform.get_form()

        self.assertEqual(result["responseCode"], 200)
        self.assertEqual(result["content"]["id"], self.form_id)

    @patch("crossmark_jotform_api.jotForm.requests.get")
    def test_get_form_failure(self, mock_get):
        """Test form retrieval failure"""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with patch.object(JotForm, "update"):
            jotform = JotForm(self.api_key, self.form_id)
            result = jotform.get_form()

        self.assertIsNone(result)

    def test_set_url_param_new_param(self):
        """Test setting a new URL parameter"""
        with patch.object(JotForm, "update"):
            jotform = JotForm(self.api_key, self.form_id)

        initial_url = jotform.url
        jotform.set_url_param("test_param", "test_value")

        self.assertIn("test_param=test_value", jotform.url)

    def test_set_url_param_existing_param(self):
        """Test updating an existing URL parameter"""
        with patch.object(JotForm, "update"):
            jotform = JotForm(self.api_key, self.form_id)

        # First set the parameter
        jotform.set_url_param("offset", "100")
        self.assertIn("offset=100", jotform.url)

        # Update the parameter
        jotform.set_url_param("offset", "200")
        self.assertIn("offset=200", jotform.url)
        self.assertNotIn("offset=100", jotform.url)

    @patch("crossmark_jotform_api.jotForm.requests.post")
    @patch("crossmark_jotform_api.jotForm.requests.get")
    @patch("crossmark_jotform_api.jotForm.requests.delete")
    def test_create_and_delete_submission(self, mock_delete, mock_get, mock_post):
        """Test creating a submission and then deleting it using __delitem__"""
        # Mock the initial update call
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "content": [],
            "resultSet": {"offset": 0, "limit": 1000},
        }
        mock_get.return_value = mock_get_response

        # Create JotForm instance
        with patch.object(JotForm, "_fetch_submissions_count", return_value=0):
            jotform = JotForm(self.api_key, self.form_id)

        # Mock the create submission response
        submission_id = "999888777"
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "content": {"submissionID": submission_id}
        }
        mock_post.return_value = mock_post_response

        # Mock the get submission by request response
        new_submission = {
            "id": submission_id,
            "form_id": self.form_id,
            "ip": "192.168.1.1",
            "created_at": "2024-01-01 12:00:00",
            "status": "ACTIVE",
            "new": "1",
            "flag": "0",
            "notes": "Test submission",
            "updated_at": "2024-01-01 12:00:00",
            "answers": {
                "1": {
                    "name": "testField",
                    "answer": "test value",
                    "text": "Test Field",
                    "type": "control_textbox",
                }
            },
        }

        mock_get_submission_response = Mock()
        mock_get_submission_response.status_code = 200
        mock_get_submission_response.json.return_value = {"content": new_submission}

        # Update mock_get to return different responses based on URL
        def get_side_effect(url, *args, **kwargs):
            if f"submission/{submission_id}" in url:
                return mock_get_submission_response
            return mock_get_response

        mock_get.side_effect = get_side_effect

        # Create submission
        submission_data = {"submission[1]": "test value"}
        result_id = jotform.create_submission(submission_data)

        # Verify submission was created
        self.assertEqual(result_id, submission_id)
        self.assertIn(submission_id, jotform.submission_data)
        initial_count = len(jotform.submission_data)

        # Mock the delete response
        mock_delete_response = Mock()
        mock_delete_response.status_code = 200
        mock_delete.return_value = mock_delete_response

        # Delete submission using __delitem__
        del jotform[submission_id]

        # Verify submission was deleted
        self.assertNotIn(submission_id, jotform.submission_data)
        self.assertNotIn(submission_id, jotform.submission_ids)
        self.assertEqual(len(jotform.submission_data), initial_count - 1)

        # Verify the delete API was called
        mock_delete.assert_called_once()
        self.assertIn(f"submission/{submission_id}", mock_delete.call_args[0][0])

    @patch("crossmark_jotform_api.jotForm.requests.get")
    @patch("crossmark_jotform_api.jotForm.requests.delete")
    def test_delitem_nonexistent_submission(self, mock_delete, mock_get):
        """Test deleting a non-existent submission raises KeyError"""
        # Mock the initial update call
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "content": [],
            "resultSet": {"offset": 0, "limit": 1000},
        }
        mock_get.return_value = mock_get_response

        # Create JotForm instance
        with patch.object(JotForm, "_fetch_submissions_count", return_value=0):
            jotform = JotForm(self.api_key, self.form_id)

        # Try to delete non-existent submission
        with self.assertRaises(KeyError):
            del jotform["nonexistent_id"]


class TestJotFormSubmission(unittest.TestCase):
    """Unit tests for JotFormSubmission"""

    def setUp(self):
        """Set up test fixtures"""
        self.api_key = "test_api_key"
        self.sample_submission = {
            "id": "123456789",
            "form_id": "987654321",
            "ip": "192.168.1.1",
            "created_at": "2024-01-01 12:00:00",
            "status": "ACTIVE",
            "new": "1",
            "flag": "0",
            "notes": "",
            "updated_at": "2024-01-01 12:00:00",
            "answers": {
                "1": {
                    "name": "fullName",
                    "answer": "John Doe",
                    "text": "Full Name",
                    "type": "control_textbox",
                },
                "2": {
                    "name": "email",
                    "answer": "john@example.com",
                    "text": "Email Address",
                    "type": "control_email",
                },
            },
        }

    def test_submission_initialization(self):
        """Test JotFormSubmission initialization"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        self.assertEqual(submission.id, "123456789")
        self.assertEqual(submission.form_id, "987654321")
        self.assertEqual(submission.ip, "192.168.1.1")
        self.assertEqual(submission.status, "ACTIVE")

    def test_get_answer_by_text(self):
        """Test getting answer by text"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        answer = submission.get_answer_by_text("Full Name")
        self.assertEqual(answer["answer"], "John Doe")
        self.assertEqual(answer["name"], "fullName")

    def test_get_answer_by_name(self):
        """Test getting answer by name"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        answer = submission.get_answer_by_name("fullName")
        self.assertEqual(answer["answer"], "John Doe")
        self.assertEqual(answer["text"], "Full Name")

    def test_get_answer_by_key(self):
        """Test getting answer by key"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        answer = submission.get_answer_by_key("1")
        self.assertEqual(answer["answer"], "John Doe")
        self.assertEqual(answer["name"], "fullName")

    def test_get_emails(self):
        """Test extracting emails from submission"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        emails = submission.get_emails()
        self.assertIn("john@example.com", emails)

    def test_get_value_with_string(self):
        """Test get_value with string input"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        result = submission.get_value("test string")
        self.assertEqual(result, "test string")

    def test_get_value_with_dict(self):
        """Test get_value with dict input"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        test_dict = {"answer": "test answer"}
        result = submission.get_value(test_dict)
        self.assertEqual(result, "test answer")

    def test_make_array_with_string(self):
        """Test make_array with string input"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        result = submission.make_array("item1, item2, item3")
        self.assertEqual(result, ["item1", "item2", "item3"])

    def test_make_array_with_list(self):
        """Test make_array with list input"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        test_list = ["item1", "item2", "item3"]
        result = submission.make_array(test_list)
        self.assertEqual(result, test_list)

    def test_split_domain_from_email(self):
        """Test splitting domain from email"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        result = submission.split_domain_from_email("test@example.com")
        self.assertEqual(result, "test")

    def test_to_dict(self):
        """Test converting submission to dict"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        result = submission.to_dict()
        self.assertEqual(result["id"], "123456789")
        self.assertEqual(result["form_id"], "987654321")
        self.assertIn("emails", result)

    def test_delitem_answer(self):
        """Test deleting an answer using __delitem__"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        # Verify answer exists before deletion
        self.assertIn("1", submission.answers)
        initial_answer_count = len(submission.answers)
        initial_arr_count = len(submission.answers_arr)

        # Delete the answer using __delitem__
        del submission["1"]

        # Verify answer was removed from both answers dict and answers_arr
        self.assertNotIn("1", submission.answers)
        self.assertEqual(len(submission.answers), initial_answer_count - 1)
        self.assertEqual(len(submission.answers_arr), initial_arr_count - 1)

        # Verify it's not in answers_arr
        for answer in submission.answers_arr:
            self.assertNotEqual(answer["key"], "1")

    def test_delitem_nonexistent_answer(self):
        """Test deleting a non-existent answer raises KeyError"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        # Try to delete non-existent answer
        with self.assertRaises(KeyError):
            del submission["999"]


if __name__ == "__main__":
    unittest.main()
