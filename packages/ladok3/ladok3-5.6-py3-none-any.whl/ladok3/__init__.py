"""A Python wrapper for the LADOK3 API"""

# -*- coding: utf-8 -*-
import cachetools
import datetime
import functools
import html
import json
import operator
import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib.parse
import weblogin.ladok


class LadokSession:
    """This is an interface for reading and writing data from and to LADOK."""

    def __init__(
        self, institution, vars=None, autologin_handlers=None, test_environment=False
    ):
        """
        Creates a session with LADOK.
        - `institution` is the name (str) of the university that will give a unique
          match when searching SeamlessAccess.org (see weblogin.ladok.SSOlogin).
        - `vars` is a dictionary that is passed to weblogin.ladok.SSOlogin to
          supply the login credentials. Usually contains keys 'username' and
          'password', see weblogin.ladok.SSOlogin documentation for details.
        - `autologin_handlers` is a list of weblogin.AutologinHandler objects
          specific to the institution. Usually one for the SAML handler and one for
          the actual login server. (For KTH it's weblogin.kth.SAMLlogin and
          weblogin.kth.UGlogin.) Default value is None, only the
          `weblogin.ladok.SSOlogin` handler will be used.
        - `test_environment` specifies whether we should use LADOK's test
          environment instead of the production environment.
        """
        self.__session = None
        if not vars:
            vars = {}
        if not autologin_handlers:
            autologin_handlers = []

        autologin_handlers.insert(
            0,
            weblogin.ladok.SSOlogin(
                institution, vars=vars, test_environment=test_environment
            ),
        )

        self.__session = weblogin.AutologinSession(autologin_handlers)
        retry_strategy = Retry(
            total=10,
            backoff_factor=1,
            backoff_max=300,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=[
                "HEAD",
                "GET",
                "PUT",
                "DELETE",
                "OPTIONS",
                "TRACE",
                "POST",
            ],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.__session.mount("http://", adapter)
        self.__session.mount("https://", adapter)
        self.cache = {}
        self.base_url = (
            "https://start.ladok.se"
            if not test_environment
            else "https://start.test.ladok.se"
        )
        self.base_gui_url = self.base_url + "/gui"
        self.base_gui_proxy_url = self.base_gui_url + "/proxy"
        self.headers = {
            "Accept": "application/vnd.ladok-resultat+json, \
    application/vnd.ladok-kataloginformation+json, \
    application/vnd.ladok-studentinformation+json, \
    application/vnd.ladok-studiedeltagande+json, \
    application/vnd.ladok-utbildningsinformation+json, \
    application/vnd.ladok-examen+json, \
    application/vnd.ladok-extintegration+json, \
    application/vnd.ladok-uppfoljning+json, \
    application/vnd.ladok-extra+json, \
    application/json, \
    text/plain"
        }
        self.__access_time = None
        self.__timeout = datetime.timedelta(minutes=15)

    @property
    def session(self):
        """A guaranteed to be active and logged in requests session to LADOK"""
        return self.__session

    @session.setter
    def session(self, new_value):
        self.__session = new_value

    @cachetools.cachedmethod(
        operator.attrgetter("cache"),
        key=functools.partial(cachetools.keys.hashkey, "grade_scale"),
    )
    def get_grade_scales(self, /, **kwargs):
        """Return a list of (un)filtered grade scales"""
        if len(kwargs) == 0:
            return [GradeScale(**scale_data) for scale_data in self.grade_scales_JSON()]

        return filter_on_keys(self.get_grade_scales(), **kwargs)

    @cachetools.cachedmethod(
        operator.attrgetter("cache"),
        key=functools.partial(cachetools.keys.hashkey, "get_student"),
    )
    def get_student(self, id):
        """Get a student by unique ID, returns a Student object"""
        # note that self is the required LadokSession object
        return Student(ladok=self, id=id)

    @cachetools.cachedmethod(
        operator.attrgetter("cache"),
        key=functools.partial(cachetools.keys.hashkey, "search_courses"),
    )
    def search_course_rounds(self, /, **kwargs):
        """Query LADOK about course rounds, possible keys:
        code, round_code, name
        """
        results = self.search_course_rounds_JSON(**kwargs)
        return [CourseRound(ladok=self, **result) for result in results]

    def get_query(self, path, content_type="application/vnd.ladok-resultat+json"):
        """
        Make GET query to LADOK server and return JSON data.

        Args:
          path: API endpoint path
          content_type: HTTP Content-Type header value

        Returns:
          JSON data from the response

        Raises:
          LadokServerError: If the server returns an error message
          LadokAPIError: If the request fails or returns an error status
        """
        headers = self.headers.copy()
        headers["Content-Type"] = content_type

        self.__access_time = datetime.datetime.now()

        response = self.session.get(url=self.base_gui_proxy_url + path, headers=headers)

        if response.ok:
            return response.json()
        try:
            error_msg = response.json()["Meddelande"]
            raise LadokServerError(error_msg)
        except:
            error_msg = response.text
        raise LadokAPIError(f"GET request to {path} failed: {error_msg}")

    def put_query(
        self, path, put_data, content_type="application/vnd.ladok-resultat+json"
    ):
        """
        Make PUT query to LADOK server and return JSON data.

        Args:
          path: API endpoint path
          put_data: Data to send in request body
          content_type: HTTP Content-Type header value

        Returns:
          JSON data from the response

        Raises:
          LadokServerError: If the server returns an error message
          LadokAPIError: If the request fails or returns an error status
        """
        headers = self.headers.copy()
        headers["Content-Type"] = content_type
        headers["X-XSRF-TOKEN"] = self.xsrf_token
        headers["Referer"] = self.base_gui_url

        response = self.session.put(
            url=self.base_gui_proxy_url + path, json=put_data, headers=headers
        )

        if response.ok:
            return response.json()
        try:
            error_msg = response.json()["Meddelande"]
            raise LadokServerError(error_msg)
        except:
            error_msg = response.text
        raise LadokAPIError(f"PUT request to {path} failed: {error_msg}")

    def post_query(
        self, path, post_data, content_type="application/vnd.ladok-resultat+json"
    ):
        """
        Make POST query to LADOK server and return JSON data.

        Args:
          path: API endpoint path
          post_data: Data to send in request body
          content_type: HTTP Content-Type header value

        Returns:
          JSON data from the response

        Raises:
          LadokServerError: If the server returns an error message
          LadokAPIError: If the request fails or returns an error status
        """
        headers = self.headers.copy()
        headers["Content-Type"] = content_type
        headers["X-XSRF-TOKEN"] = self.xsrf_token
        headers["Referer"] = self.base_gui_url

        response = self.session.post(
            url=self.base_gui_proxy_url + path, json=post_data, headers=headers
        )

        if response.ok:
            return response.json()
        try:
            error_msg = response.json()["Meddelande"]
            raise LadokServerError(error_msg)
        except:
            error_msg = response.text
        raise LadokAPIError(f"POST request to {path} failed: {error_msg}")

    def del_query(self, path):
        """
        Returns DELETE query response for path on the LADOK server.

        Args:
            path (str): API endpoint path

        Returns:
          True, if success but no content is returned.
          JSON data from the response, if any.
          Otherwise the response object.

        Raises:
            LadokServerError: If the server returns an error message
            LadokAPIError: If the request fails or returns an error status
        """
        headers = self.headers.copy()
        headers["X-XSRF-TOKEN"] = self.xsrf_token

        response = self.session.delete(
            url=self.base_gui_proxy_url + path, headers=headers
        )

        if response.status_code == requests.codes.no_content:
            return True
        if response.ok:
            try:
                return response.json()
            except:
                return response
        try:
            error_msg = response.json()["Meddelande"]
            raise LadokServerError(error_msg)
        except:
            error_msg = response.text
        raise LadokAPIError(f"DELETE request to {path} failed: {error_msg}")

    @property
    def xsrf_token(self):
        """
        Get a fresh XSRF token for authenticated requests.

        LADOK requires XSRF tokens for PUT, POST, and DELETE requests. This property
        ensures the token is fresh and valid, triggering a re-login if necessary.

        Returns:
            str: A valid XSRF token for use in authenticated requests.
        """
        if (
            not self.__access_time
            or datetime.datetime.now() - self.__access_time > self.__timeout
        ):
            self.user_info_JSON()  # trigger login
        else:
            self.__access_time = datetime.datetime.now()

        cookies = self.session.cookies.get_dict()
        return cookies["XSRF-TOKEN"]

    def grade_scales_JSON(self):
        """
        Fetch all grading scales from LADOK.

        Returns:
            list: A list of JSON objects containing grading scale data from LADOK.

        Raises:
            Exception: If the request fails or returns an error status.
        """
        data = self.get_query(
            "/kataloginformation/internal/grunddata/betygsskala",
            content_type="application/vnd.ladok-kataloginformation+json;charset=UTF-8",
        )

        try:
            return data["Betygsskala"]
        except KeyError as err:
            err.add_note(f"Response data: {data}")
            raise LadokAPIError(
                f"Unexpected response format when fetching grading scales: "
                f"missing 'Betygsskala' key"
            ) from err

    #####################################################################
    #
    # get_student_data_JSON
    #
    # person_nr          - personnummer, flera format accepteras enligt regex:
    #                      (\d\d)?(\d\d)(\d\d\d\d)[+\-]?(\w\w\w\w)
    #
    # lang               - language code 'en' or 'sv', defaults to 'sv'
    #
    # RETURNERAR en dictionary med för- och efternamn and more
    def get_student_data_JSON(self, person_nr_raw, lang="sv"):
        """
        Get student data from LADOK using a Swedish personal number (personnummer).

        Args:
            person_nr_raw (str): Swedish personal number in format YYYYMMDD-XXXX or similar
            lang (str, optional): Language code 'en' or 'sv'. Defaults to 'sv'.

        Returns:
            dict: Student data dictionary containing name, contact info, and more.

        Raises:
            Exception: If the personal number format is invalid.
            ValueError: If student cannot be found or multiple matches found.
        """
        person_nr = format_personnummer(person_nr_raw)

        if not person_nr:
            raise LadokValidationError("Invalid person nr " + person_nr_raw)

        response = self.session.get(
            url=self.base_gui_proxy_url
            + "/studentinformation/internal/student/filtrera"
            f"?personnummer={person_nr}"
            "&limit=2&page=1"
            "&orderby=EFTERNAMN_ASC&orderby=FORNAMN_ASC"
            "&orderby=PERSONNUMMER_ASC",
            headers=self.headers,
        )

        if response.status_code == requests.codes.ok:
            record = response.json()["Resultat"]
        else:
            raise ValueError(
                f"can't find student based on personnummer {person_nr}: "
                f"bad response: {response.text}"
            )

        if len(record) != 1:
            raise ValueError(
                f"can't find student based on personnummer {person_nr}: "
                f"not a unique match: {record}"
            )

        return record[0]

    #####################################################################
    #
    # get_student_data_by_uid_JSON
    #
    # uid                - Ladok ID
    #
    # RETURNERAR en dictionary med för- och efternamn and more
    def get_student_data_by_uid_JSON(self, uid):
        """
        Get student data from LADOK using a LADOK UID.

        Args:
            uid (str): The student's unique LADOK identifier.

        Returns:
            dict: Student data dictionary containing personal information.

        Raises:
            AttributeError: If student cannot be found by the given UID.
        """
        data = self.get_query(
            f"/studentinformation/internal/student/{uid}",
            content_type="application/vnd.ladok-studentinformation+json;charset=UTF-8",
        )

        return data

    def get_student_contact_data_JSON(self, student_id):
        """
        Returns contact data for student with student_id, returns JSON
        """
        try:
            return self.get_query(
                f"/studentinformation/internal/student/{student_id}/kontaktuppgifter",
                "application/vnd.ladok-studentinformation+json",
            )
        except LadokAPIError as err:
            raise LadokAPIError(
                f"Failed to get contact data for " f"student {student_id}: {err}"
            ) from err
        except LadokServerError as err:
            raise LadokServerError(
                f"LADOK server error when getting contact data for "
                f"student {student_id}: {err}"
            ) from err

    def get_student_suspensions_JSON(self, student_id):
        """
        Returns suspensions from studies for student with student_id,
        returns JSON
        """
        try:
            return self.get_query(
                f"/studentinformation/internal/avstangning/student/{student_id}",
                "application/vnd.ladok-studentinformation+json",
            )
        except LadokAPIError as err:
            raise LadokAPIError(
                f"Failed to get suspensions for " f"student {student_id}: {err}"
            ) from err
        except LadokServerError as err:
            raise LadokServerError(
                f"LADOK server error when getting suspensions for "
                f"student {student_id}: {err}"
            ) from err

    def registrations_JSON(self, student_id):
        """
        Return all registrations for student with ID student_id.
        """
        data = self.get_query(
            "/studiedeltagande/internal/tillfallesdeltagande/kurstillfallesdeltagande"
            f"/student/{student_id}",
            "application/vnd.ladok-studiedeltagande+json",
        )

        try:
            return data["Tillfallesdeltaganden"]
        except KeyError as err:
            err.add_note(f"Response data: {data}")
            raise LadokAPIError(
                f"Unexpected response format when fetching registrations for "
                f"student {student_id}: missing 'Tillfallesdeltaganden' key"
            ) from err

    def registrations_on_course_JSON(self, course_education_id, student_id):
        """
        Return a list of registrations on course with education_id for student with
        student_id. JSON format.
        """
        data = self.get_query(
            "/studiedeltagande/internal/tillfallesdeltagande"
            f"/utbildning/{course_education_id}/student/{student_id}",
            "application/vnd.ladok-studiedeltagande+json",
        )

        try:
            return data["Tillfallesdeltaganden"]
        except KeyError as err:
            err.add_note(f"Response data: {data}")
            raise LadokAPIError(
                f"Unexpected response format when fetching registrations for "
                f"student {student_id} on course {course_education_id}: "
                f"missing 'Tillfallesdeltaganden' key"
            ) from err

    # added by GQMJr
    def studystructure_student_JSON(self, uid):
        """
        Returns a dictionary of student information. This contains programmes that
        the student is admitted to.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/studiedeltagande/internal/studiestruktur/student/"
            + uid,
            headers=self.headers,
        )
        if r.status_code == 200:
            return r.json()
        raise LadokAPIError(f"can't get study structure for student {uid}: {r.text}")

    def search_course_rounds_JSON(self, /, **kwargs):
        """Query LADOK about course rounds, possible keys:
        code, round_code, name
        """
        url = "/resultat/internal/kurstillfalle/filtrera?"

        if "code" in kwargs:
            url += f"kurskod={kwargs['code']}&"
        if "name" in kwargs:
            url += f"benamning={kwargs['name']}&"
        if "round_code" in kwargs:
            url += f"tillfalleskod={kwargs['round_code']}&"

        url += "page=1&limit=400&sprakkod=sv"

        data = self.get_query(url)

        try:
            return data["Resultat"]
        except KeyError as err:
            err.add_note(f"Response data: {data}")
            raise LadokAPIError(
                f"Unexpected response format when searching for course rounds: "
                f"missing 'Resultat' key"
            ) from err

    def course_rounds_JSON(self, course_instance_id):
        """Requires course instance ID"""
        data = self.get_query(
            f"/resultat/internal/kurstillfalle/kursinstans/{course_instance_id}"
        )

        try:
            return data["Utbildningstillfalle"]
        except KeyError as err:
            err.add_note(f"Response data: {data}")
            raise LadokAPIError(
                f"Unexpected response format when fetching course rounds for "
                f"instance {course_instance_id}: missing 'Utbildningstillfalle' key"
            ) from err

    def course_instance_JSON(self, instance_id):
        """
        Returns course instance data for a course with instance ID instance_id
        """
        try:
            return self.get_query(
                f"/resultat/internal/utbildningsinstans/kursinstans/{instance_id}"
            )
        except LadokAPIError as err:
            raise LadokAPIError(
                f"Failed to get course instance data for " f"{instance_id}: {err}"
            ) from err
        except LadokServerError as err:
            raise LadokServerError(
                f"LADOK server error when getting course instance data for "
                f"{instance_id}: {err}"
            ) from err

    # added by GQMJr
    def course_instances_JSON(self, course_code, lang="sv"):
        """
        Returns a list of dictionaries with course instances for a given course code.
        The course code is a string such as "DD1310". The language code is 'en' or
        'sv'.

        Note that there seems to be a limit of 403 for the number of pages.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/resultat/internal/kurstillfalle/filtrera?kurskod="
            + course_code
            + "&page=1&limit=100&skipCount=false&sprakkod="
            + lang,  # not sure about this one /CO
            headers=self.headers,
        )
        if r.status_code == requests.codes.ok:
            return r.json()
        raise LadokAPIError(
            f"failed to get course instances for {course_code}: {r.text}"
        )

    # added by GQMJr
    def instance_info(self, course_code, instance_code, lang="sv"):
        """
        Returns a dictionary of course instance information.

        course_code        - course code, such as "DD1310"

        instance_code      - instance of the course ('TillfallesKod')

        lang               - language code 'en' or 'sv', defaults to 'sv'
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/resultat/internal/kurstillfalle/filtrera?kurskod="
            + course_code
            + "&page=1&limit=25&skipCount=false&sprakkod="
            + lang,
            headers=self.headers,
        )
        if r.status_code == requests.codes.ok:
            rj = r.json()
            for course in rj["Resultat"]:
                if course["TillfallesKod"] == instance_code:
                    return course
            # If we get here, the course instance was not found
            raise LadokNotFoundError(
                f"course instance {instance_code} not found for course {course_code}"
            )
        raise LadokAPIError(
            f"failed to search for course instance {course_code}/{instance_code}: {r.text}"
        )

    # added by GQMJr
    def instance_info_uid(self, instance_uid):
        """
        Returns a dictionary of course instance information.

        instance_uid: course's Uid (from course_integration_id or
                      sis_course_id in Canvas)
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/resultat/internal/kurstillfalle/"
            + instance_uid,
            headers=self.headers,
        )
        if r.status_code == requests.codes.ok:
            return r.json()
        raise LadokAPIError(
            f"failed to get course instance info for {instance_uid}: {r.text}"
        )

    def course_round_components_JSON(self, round_id):
        """
        Fetch course components for a given course round.

        Args:
            round_id (str): The unique identifier of the course round.

        Returns:
            list: A list of course component JSON objects.

        Raises:
            LadokServerError: If the request fails or server returns an error message.
        """
        data = self.put_query(
            "/resultat/internal/kurstillfalle/moment", {"Identitet": [round_id]}
        )

        try:
            return data["MomentPerKurstillfallen"][0]["Moment"]
        except (KeyError, IndexError) as err:
            err.add_note(f"Response data: {data}")
            raise LadokAPIError(
                f"Unexpected response format when fetching components for "
                f"round {round_id}: {type(err).__name__}"
            ) from err

    def course_instance_components_JSON(self, course_instance_id):
        """
        Fetch course components for a given course instance.

        Args:
            course_instance_id (str): The unique identifier of the course instance.

        Returns:
            dict: JSON object containing course instance components.

        Raises:
            LadokServerError: If the request fails or server returns an error message.
        """
        data = self.put_query(
            "/resultat/internal/utbildningsinstans/moduler",
            {"Identitet": [course_instance_id]},
        )

        try:
            return data["Utbildningsinstans"][0]
        except (KeyError, IndexError) as err:
            err.add_note(f"Response data: {data}")
            raise LadokAPIError(
                f"Unexpected response format when fetching components for "
                f"instance {course_instance_id}: {type(err).__name__}"
            ) from err

    def search_reported_results_JSON(self, course_round_id, component_instance_id):
        """Requires:
        course_round_id: round_id for a course,
        component_instance_id: instance_id for a component of the course.
        """
        put_data = {
            "Filtrering": ["OBEHANDLADE", "UTKAST", "ATTESTERADE"],
            "KurstillfallenUID": [course_round_id],
            "OrderBy": ["EFTERNAMN_ASC", "FORNAMN_ASC", "PERSONNUMMER_ASC"],
            "Limit": 400,
            "Page": 1,
            "StudenterUID": [],
        }

        data = self.put_query(
            "/resultat/internal/studieresultat/rapportera"
            f"/utbildningsinstans/{component_instance_id}/sok",
            put_data,
        )

        try:
            return data["Resultat"]
        except KeyError as err:
            err.add_note(f"Response data: {data}")
            raise LadokAPIError(
                f"Unexpected response format when searching for results for "
                f"round {course_round_id}, component {component_instance_id}: "
                f"missing 'Resultat' key"
            ) from err

    def search_course_results_JSON(self, course_round_id, component_instance_id):
        """
        Retrieve course results for a specific component in a course round.

        Args:
            course_round_id (str): The unique identifier of the course round.
            component_instance_id (str): The unique identifier of the component instance.

        Returns:
            list: List of course result JSON objects.

        Raises:
            LadokAPIError: If the request fails.
        """
        put_data = {
            "KurstillfallenUID": [course_round_id],
            "Tillstand": ["REGISTRERAD", "AVKLARAD", "AVBROTT"],
            "OrderBy": ["EFTERNAMN_ASC", "FORNAMN_ASC"],
            "Limit": 400,
            "Page": 1,
        }

        data = self.put_query(
            "/resultat/internal/resultatuppfoljning/resultatuppfoljning/sok", put_data
        )

        try:
            return data["Resultat"]
        except KeyError as err:
            err.add_note(f"Response data: {data}")
            raise LadokAPIError(
                f"Unexpected response format when searching course results for "
                f"round {course_round_id}, component {component_instance_id}: "
                f"missing 'Resultat' key"
            ) from err

    def student_results_JSON(self, student_id, course_education_id):
        """Returns the results for a student on a course"""
        try:
            return self.get_query(
                "/resultat/internal/studentenskurser/kursinformation"
                f"/student/{student_id}/kursUID/{course_education_id}"
            )
        except LadokAPIError as err:
            raise LadokAPIError(
                f"Failed to get results for student {student_id} "
                f"on course {course_education_id}: {err}"
            ) from err
        except LadokServerError as err:
            raise LadokServerError(
                f"LADOK server error when getting results for "
                f"student {student_id} on course {course_education_id}: "
                f"{err}"
            ) from err

    def create_result_JSON(
        self,
        student_id,
        course_instance_id,
        component_id,
        grade_id,
        date,
        project_title=None,
    ):
        """
        Creates a new result
        """
        try:
            return self.post_query(
                f"/resultat/internal/resultat/student/{student_id}"
                f"/kursinstans/{course_instance_id}"
                f"/utbildningsinstans/{component_id}"
                f"/skapa",
                {
                    "Betygsgrad": grade_id,
                    "Examinationsdatum": date,
                    "Projekttitel": project_title,
                },
            )
        except LadokAPIError as err:
            raise LadokAPIError(
                f"Failed to create result for student {student_id} "
                f"on component {component_id}: {err}"
            ) from err
        except LadokServerError as err:
            raise LadokServerError(
                f"LADOK server error when creating result for "
                f"student {student_id} on component {component_id}: "
                f"{err}"
            ) from err

    def update_result_JSON(self, result_id, grade_id, date, last_modified, notes=[]):
        """Update an existing result draft in LADOK.

        Note: Cannot be used to update finalized results. Uses ResultatUID, not StudieresultatUID.

        Args:
            result_id (str): The unique result identifier (ResultatUID).
            grade_id (int): The numeric grade identifier from the grade scale.
            date (str): Examination date in YYYY-MM-DD format.
            last_modified (str): Last modification timestamp to prevent conflicts.
            notes (list, optional): List of notes to attach to the result.

        Returns:
            dict: Updated result data from LADOK.

        Raises:
            Exception: If the update request fails or is rejected by LADOK.
        """
        try:
            return self.put_query(
                f"/resultat/internal/resultat/uppdatera/{result_id}",
                {
                    "Betygsgrad": grade_id,
                    "Examinationsdatum": date,
                    "Noteringar": notes,
                    "SenasteResultatandring": last_modified,
                },
            )
        except LadokAPIError as err:
            raise LadokAPIError(f"Failed to update result {result_id}: {err}") from err
        except LadokServerError as err:
            raise LadokServerError(
                f"LADOK server error when updating result " f"{result_id}: {err}"
            ) from err

    def result_attestants_JSON(self, result_id):
        """Returns a list of result attestants"""
        data = self.put_query(
            "/resultat/internal/anvandare/resultatrattighet/attestanter/kurstillfallesrapportering",
            {"Identitet": [result_id]},
        )

        try:
            return data["Anvandare"]
        except KeyError as err:
            err.add_note(f"Response data: {data}")
            raise LadokAPIError(
                f"Unexpected response format when fetching attestants for "
                f"result {result_id}: missing 'Anvandare' key"
            ) from err

    def result_reporters_JSON(self, organization_id):
        """Returns a list of who can report results in an organization"""
        data = self.get_query(
            "/kataloginformation/internal/anvandare/organisation/"
            + organization_id
            + "/resultatrapportorer",
            "application/vnd.ladok-kataloginformation+json",
        )

        try:
            return data["Anvandare"]
        except KeyError as err:
            err.add_note(f"Response data: {data}")
            raise LadokAPIError(
                f"Unexpected response format when fetching reporters for "
                f"organization {organization_id}: missing 'Anvandare' key"
            ) from err

    def user_info_JSON(self):
        """
        Get information about the currently logged-in user.

        Returns:
            dict: User information including name, roles, and permissions.

        Raises:
            Exception: If the request fails or returns an error status.
        """
        try:
            return self.get_query(
                "/kataloginformation/internal/anvandare/anvandarinformation",
                "application/vnd.ladok-kataloginformation+json",
            )
        except LadokAPIError as err:
            raise LadokAPIError(f"Failed to get user info: {err}") from err
        except LadokServerError as err:
            raise LadokServerError(
                f"LADOK server error when getting user info: " f"{err}"
            ) from err

    def finalize_result_JSON(
        self, result_id, last_modified, reporter_id, attestant_ids=[], others=[]
    ):
        """Marks a result as finalized (klarmarkera)"""
        try:
            return self.put_query(
                f"/resultat/internal/resultat/klarmarkera/{result_id}",
                {
                    "Beslutsfattare": attestant_ids,
                    "KlarmarkeradAvUID": reporter_id,
                    "RattadAv": [],
                    "OvrigaMedverkande": "\n".join(set(others)),
                    "ResultatetsSenastSparad": last_modified,
                },
            )
        except LadokAPIError as err:
            raise LadokAPIError(
                f"Failed to finalize result {result_id}: {err}"
            ) from err
        except LadokServerError as err:
            raise LadokServerError(
                f"LADOK server error when finalizing result " f"{result_id}: {err}"
            ) from err

    def update_finalized_result_JSON(
        self, result_id, grade_id, date, last_modified, notes=[]
    ):
        try:
            return self.put_query(
                f"/resultat/internal/resultat/uppdateraklarmarkerat/{result_id}",
                {
                    "Betygsgrad": grade_id,
                    "Examinationsdatum": date,
                    "Noteringar": notes,
                    "SenasteResultatandring": last_modified,
                },
            )
        except LadokAPIError as err:
            raise LadokAPIError(
                f"Failed to update finalized result {result_id}: " f"{err}"
            ) from err
        except LadokServerError as err:
            raise LadokServerError(
                f"LADOK server error when updating finalized result "
                f"{result_id}: {err}"
            ) from err

    def finalized_result_to_draft_JSON(self, result_id, last_modified):
        try:
            return self.put_query(
                f"/resultat/internal/resultat/tillbakatillutkast/{result_id}",
                {"ResultatUID": result_id, "ResultatetsSenastSparad": last_modified},
            )
        except LadokAPIError as err:
            raise LadokAPIError(
                f"Failed to change finalized result {result_id} to draft: " f"{err}"
            ) from err
        except LadokServerError as err:
            raise LadokServerError(
                f"LADOK server error when changing finalized result "
                f"{result_id} to draft: {err}"
            ) from err

    def remove_result_draft_JSON(self, result_id):
        try:
            data = self.del_query(f"/resultat/internal/resultat/tabort/{result_id}")
        except LadokAPIError as err:
            raise LadokAPIError(
                f"LADOK request to remove draft result " f"{result_id} failed: {err}"
            ) from err
        except LadokServerError as err:
            raise LadokServerError(
                f"LADOK server error when removing "
                f"draft result {result_id}: "
                f"{err}"
            ) from err

    def participants_JSON(self, course_round_id, /, **kwargs):
        """Returns JSON record containing participants in a course identified by
        round ID.
        Filters in kwargs: not_started, ongoing, registered, finished, cancelled"""
        participants_types = []
        if "not_started" in kwargs and kwargs["not_started"]:
            participants_types.append("EJ_PABORJAD")
        if "ongoing" in kwargs and kwargs["ongoing"]:
            participants_types.append("PAGAENDE")
        if "registered" in kwargs and kwargs["registered"]:
            participants_types.append("REGISTRERAD")
        if "finished" in kwargs and kwargs["finished"]:
            participants_types.append("AVKLARAD")
        if "cancelled" in kwargs and kwargs["cancelled"]:
            participants_types.append("AVBROTT")
        # 'ATERBUD', # Withdrawal
        # 'PAGAENDE_MED_SPARR', # on-going block exists
        # 'EJ_PAGAENDE_TILLFALLESBYTE', # not on-going due to instance exchange
        # 'UPPEHALL', # not on-going due to approved leave from studies

        if not kwargs:
            participants_types = ["PAGAENDE", "REGISTRERAD", "AVKLARAD"]

        put_data = {
            "page": 1,
            "limit": 400,
            "orderby": [
                "EFTERNAMN_ASC",
                "FORNAMN_ASC",
                "PERSONNUMMER_ASC",
                "KONTROLLERAD_KURS_ASC",
            ],
            "deltagaretillstand": participants_types,
            "utbildningstillfalleUID": [course_round_id],
        }

        response = self.put_query(
            "/studiedeltagande/internal/deltagare/kurstillfalle",
            put_data,
            "application/vnd.ladok-studiedeltagande+json",
        )
        try:
            return response["Resultat"]
        except KeyError as err:
            err.add_note(f"Response data: {response}")
            raise LadokAPIError(
                f"Unexpected response format when fetching participants for "
                f"round {course_round_id}: missing 'Resultat' key"
            ) from err

    # added by GQMJr
    def grading_rights(self):
        """
        Returns a list of dictionaries with the grading rights of the logged in user.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/resultat/internal/resultatrattighet/listaforinloggadanvandare",
            headers=self.headers,
        )
        if r.status_code == requests.codes.ok:
            return r.json()["Resultatrattighet"]
        raise LadokAPIError(f"failed to get grading rights: {r.text}")

    # added by GQMJr
    def organization_info_JSON(self):
        """
        Returns a dictionary of organization information for the entire institution
        of the logged in user.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url + "/resultat/internal/organisation/utanlankar",
            headers=self.headers,
        )
        if r.status_code == requests.codes.ok:
            return r.json()
        raise LadokAPIError(f"failed to get organization info: {r.text}")

    # added by GQMJr
    def larosatesinformation_JSON(self):
        """
        Returns a dictionary of the university or college information.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/internal/grunddata/larosatesinformation",
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def undervisningssprak_JSON(self):
        """
        Returns a dictionary of teaching languages.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/internal/grunddata/undervisningssprak",
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def i18n_translation_JSON(self, lang="sv"):
        """
        Returns a dictionary of i18n translations used in Ladok3.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/internal/i18n/oversattningar/sprakkod/"
            + lang,
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def svenskorter_JSON(self):
        """
        Returns a dictionary of Swedish places with their KommunID.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/internal/grunddata/svenskort",
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def kommuner_JSON(self):
        """
        Returns a dictionary of Swedish municipalities.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/internal/grunddata/kommun",
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def lander_JSON(self):
        """
        Returns a dictionary of countries.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url + "/kataloginformation/internal/grunddata/land",
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def undervisningstid_JSON(self):
        """
        Returns a dictionary of teaching times.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/internal/grunddata/undervisningstid",
            headers=self.headers,
        ).json()
        return r

    # RETURNERAR JSON of Successive Specializations
    def successivfordjupning_JSON(self):
        """
        Returns a dictionary of Successive Specializations.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/internal/grunddata/successivfordjupning",
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def undervisningsform_JSON(self):
        """
        Returns forms of education.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/internal/grunddata/undervisningsform",
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def LokalaPerioder_JSON(self):
        """
        Returns local periods.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/internal/grunddata/period",
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def nivainomstudieordning_JSON(self):
        """
        Returns education levels.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/internal/grunddata/nivainomstudieordning",
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def amnesgrupp_JSON(self):
        """
        Returns subject area groups.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/internal/grunddata/amnesgrupp",
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def studietakt_JSON(self):
        """
        Returns study paces.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/internal/grunddata/studietakt",
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def finansieringsform_JSON(self):
        """
        Returns forms of financing.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/internal/grunddata/finansieringsform",
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def utbildningsomrade_JSON(self):
        """
        Returns subject areas.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/internal/grunddata/utbildningsomrade",
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def kravpatidigarestudier_JSON(self):
        """
        Returns requirements for earlier studies.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/internal/grunddata/kravpatidigarestudier",
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def studieordning_JSON(self):
        """
        Returns study regulations.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/internal/grunddata/studieordning",
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def enhet_JSON(self):
        """
        Returns credit units.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/internal/grunddata/enhet",
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def studielokalisering_JSON(self):
        """
        Returns study locations.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/internal/grunddata/studielokalisering",
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def antagningsomgang_JSON(self):
        """
        Returns the admission round.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/internal/grunddata/antagningsomgang",
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def utbildningstyp_JSON(self):
        """
        Returns types of education.

        For information about these, see

          https://ladok.se/wp-content/uploads/2018/01/Funktionsbeskrivning_095.pdf
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/internal/grunddata/utbildningstyp",
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def aktivitetstillfallestyp_JSON(self):
        """
        Returns the activity types.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/internal/grunddata/aktivitetstillfallestyp",
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def catalog_service_index_JSON(self):
        """
        Returns the catalog service index.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url + "/kataloginformation/internal/service/index",
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def omradesbehorighet_JSON(self):
        """
        Returns områdesbehörighet. See

          https://antagning.se/globalassets/omradesbehorigheter-hogskolan.pdf

        for more information.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/internal/grunddata/omradesbehorighet",
            headers=self.headers,
        ).json()
        return r

    ##############################################################
    #
    # LadokSession
    #
    # get_results      returnerar en dictionary med momentnamn och resultat
    # save_result      sparar resultat för en student som utkast
    #
    # The original LadokSession code is from Alexander Baltatzis <alba@kth.se> on
    # 2020-07-20
    #
    # I (Gerald Q. Maguire Jr.) have extended on 2020-07-21 and later with the code
    # as noted below.
    #
    # I (Daniel Bosk) adapted (on 2021-01-08) the methods to a refactored
    # LadokSession class.

    #####################################################################
    #
    # get_results
    #
    # person_nr          - personnummer, siffror i strängformat
    #            t.ex. 19461212-1212
    # course_code          - kurskod t.ex. DD1321
    #
    # RETURNERAR en dictionary från ladok med momentnamn, resultat
    #
    # {'LABP': {'date': '2019-01-14', 'grade': 'P', 'status': 'attested'},
    #  'LABD': {'date': '2019-03-23', 'grade': 'E', 'status': 'pending(1)'},
    #  'TEN1': {'date': '2019-03-13', 'grade': 'F', 'status': 'pending(2)'}}
    #
    #  status:  kan ha följande värden vilket gissningsvis betyder:
    #           attested   - attesterad
    #           pending(1) - utkast
    #           pending(2) - klarmarkerad
    #
    def get_results(self, person_nr_raw, course_code):
        person_nr_raw = str(person_nr_raw)
        person_nr = format_personnummer(person_nr_raw)
        if not person_nr:
            raise LadokValidationError("Invalid person nr " + person_nr_raw)

        student_data = self.__get_student_data(person_nr)

        student_course = next(
            x
            for x in self.__get_student_courses(student_data["id"])
            if x["code"] == course_code
        )

        # get attested results
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/resultat/studentresultat/attesterade/student/"
            + student_data["id"],
            headers=self.headers,
        ).json()

        results_attested_current_course = None
        results = {}  # return value

        for course in r["StudentresultatPerKurs"]:
            if course["KursUID"] == student_course["education_id"]:
                results_attested_current_course = course["Studentresultat"]
                break

        if results_attested_current_course:
            for result in results_attested_current_course:
                try:
                    d = {
                        "grade": result["Betygsgradskod"],
                        "status": "attested",
                        "date": result["Examinationsdatum"],
                    }
                    results[result["Utbildningskod"]] = d
                except:
                    pass  # tillgodoräknanden har inga betyg och då är result['Utbildningskod'] == None

        # get pending results
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/resultat/resultat/resultat/student/"
            + student_data["id"]
            + "/kurs/"
            + student_course["education_id"]
            + "?resultatstatus=UTKAST&resultatstatus=KLARMARKERAT",
            headers=self.headers,
        ).json()

        for result in r["Resultat"]:
            r = self.session.get(
                url=self.base_gui_proxy_url
                + "/resultat/utbildningsinstans/"
                + result["UtbildningsinstansUID"],
                headers=self.headers,
            ).json()
            d_grade = result["Betygsgradsobjekt"]["Kod"]
            d_status = "pending(" + str(result["ProcessStatus"]) + ")"
            # utkast har inte datum tydligen ...
            d_date = (
                "0"
                if "Examinationsdatum" not in result
                else result["Examinationsdatum"]
            )
            d = {"grade": d_grade, "status": d_status, "date": d_date}
            results[r["Utbildningskod"]] = d
        return results

    #####################################################################
    #
    # save_result
    #
    # person_nr           - personnummer, flera format accepteras enligt regex:
    #                       (\d\d)?(\d\d)(\d\d\d\d)[+\-]?(\w\w\w\w)
    # course_code         - kurskod t.ex. DD1321
    # course_moment       - ladokmoment/kursbetyg t.ex. TEN1, LAB1, DD1321 (!)
    #                       om labmomententet är samma som course_code så sätts kursbetyg!
    # result_date         - betygsdatum, flera format accepteras enligt regex
    #                       (\d\d)?(\d\d)-?(\d\d)-?(\d\d)
    # grade_code          - det betyg som ska sättas
    # grade_scale         - betygsskala t.ex. AF eller PF. Möjliga betygsskalor
    #                       listas i self.__grade_scales.
    #
    # RETURNERAR True om det gått bra, kastar (förhoppningsvis) undantag
    #            om det går dåligt.
    def save_result(
        self,
        person_nr_raw,
        course_code,
        course_moment,
        result_date_raw,
        grade_raw,
        grade_scale,
    ):
        if grade_raw in ["AF", "PF"]:
            raise LadokValidationError(
                "Invalid grade: " + grade_raw + " looks like a grade_scale"
            )

        if (grade_raw == "P" and grade_scale == "AF") or (
            grade_raw in "ABCDE" and grade_scale == "PF"
        ):
            raise LadokValidationError(
                "Invalid grade: "
                + grade_raw
                + " does not match grade_scale "
                + grade_scale
            )

        person_nr = format_personnummer(person_nr_raw)
        if not person_nr:
            raise LadokValidationError("Invalid person nr " + person_nr_raw)

        result_date = self.__validate_date(result_date_raw)
        if not result_date:
            raise LadokValidationError(
                "Invalid grade date: "
                + result_date_raw
                + " pnr: "
                + person_nr_raw
                + " moment: "
                + course_moment
            )

        student_data = self.__get_student_data(person_nr)
        student_course = next(
            x
            for x in self.__get_student_courses(student_data["id"])
            if x["code"] == course_code
        )

        # momentkod = kurskod => vi hanterar kursbetyg
        if course_moment == student_course["code"]:
            course_moment_id = student_course["instance_id"]
        else:
            for x in self.__get_student_course_moments(
                student_course["round_id"], student_data["id"]
            ):
                if x["code"] == course_moment:
                    course_moment_id = x["course_moment_id"]

        student_course_results = self.__get_student_course_results(
            student_course["round_id"], student_data["id"]
        )

        grade_scale = self.__get_grade_scale_by_code(grade_scale)
        grade = grade_scale.grades(code=grade_raw)[0]

        headers = self.headers.copy()
        headers["Content-Type"] = "application/vnd.ladok-resultat+json"
        headers["X-XSRF-TOKEN"] = self.__get_xsrf_token()
        headers["Referer"] = self.base_gui_url

        previous_result = None

        for result in student_course_results["results"]:
            if result["pending"] is not None:
                if result["pending"]["moment_id"] == course_moment_id:
                    previous_result = result["pending"]
                    break

        # uppdatera befintligt utkast
        if previous_result:
            put_data = {
                "Resultat": [
                    {
                        "ResultatUID": previous_result["id"],
                        "Betygsgrad": grade.id,
                        "Noteringar": [],
                        "BetygsskalaID": grade_scale.id,
                        "Examinationsdatum": result_date,
                        "SenasteResultatandring": previous_result["last_modified"],
                    }
                ]
            }

            r = self.session.put(
                url=self.base_gui_proxy_url + "/resultat/studieresultat/uppdatera",
                json=put_data,
                headers=headers,
            )

        # lägg in nytt betygsutkast
        else:
            post_data = {
                "Resultat": [
                    {
                        "StudieresultatUID": student_course_results["id"],
                        "UtbildningsinstansUID": course_moment_id,
                        "Betygsgrad": grade.id,
                        "Noteringar": [],
                        "BetygsskalaID": grade_scale.id,
                        "Examinationsdatum": result_date,
                    }
                ]
            }
            r = self.session.post(
                url=self.base_gui_proxy_url + "/resultat/studieresultat/skapa",
                json=post_data,
                headers=headers,
            )

        if not "Resultat" in r.json():
            raise LadokServerError(
                "Couldn't register "
                + course_moment
                + "="
                + grade_raw
                + " "
                + result_date_raw
                + ": "
                + r.json()["Meddelande"]
            )

        return True

    #####################################################################
    #
    # get_student_data
    #
    # person_nr           - personnummer, flera format accepteras enligt regex:
    #                       (\d\d)?(\d\d)(\d\d\d\d)[+\-]?(\w\w\w\w)
    #
    # RETURNERAR {'id': 'xxxx', 'first_name': 'x', 'last_name': 'y', 'person_nr': 'xxx', 'alive': True}

    def get_student_data(self, person_nr_raw):
        person_nr = format_personnummer(person_nr_raw)

        if not person_nr:
            raise LadokValidationError("Invalid person nr " + person_nr_raw)

        student_data = self.__get_student_data(person_nr)
        return student_data

    #####################################################################
    #
    # get_student_name
    #
    # person_nr          - personnummer, flera format accepteras enligt regex:
    #                      (\d\d)?(\d\d)(\d\d\d\d)[+\-]?(\w\w\w\w)
    #
    # RETURNERAR en dictionary med för- och efternamn
    #
    # {"first_name" : 'Anna', "last_name : 'Andersson'}
    #
    def get_student_name(self, person_nr_raw):
        person_nr = format_personnummer(person_nr_raw)

        if not person_nr:
            raise LadokValidationError("Invalid person nr " + person_nr_raw)

        student_data = self.__get_student_data(person_nr)
        return {
            "first_name": student_data["first_name"],
            "last_name": student_data["last_name"],
        }

    # added by GQMJr
    #####################################################################
    #
    # all_grading_scale
    #
    #
    # RETURNERAR en dictionary of the grading scales
    def all_grading_scale(self):
        return self.get_grade_scales()

    # added by GQMJr
    #####################################################################
    #
    # change_locale
    #
    # lang               - language code 'en' or 'sv', defaults to 'sv'
    #
    # RETURNERAR reponse to the request
    def change_locale(self, lang="sv"):
        r = self.session.get(
            url=self.base_gui_url + "/services/i18n/changeLocale?lang=" + lang,
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    #####################################################################
    #
    # period_info_JSON
    #
    # RETURNERAR JSON of /resultat/grunddata/period
    def period_info_JSON(self):
        r = self.session.get(
            url=self.base_gui_proxy_url + "/resultat/internal/grunddata/period",
            # doesn't work, but also not after adding 'internal/' between 'resultat/'
            # and 'grunddata' /CO
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    #####################################################################
    #
    # organisation_by_uid_JSON
    #
    # organisationUid           -- organization's UID
    #
    # RETURNERAR JSON of selected organization
    def organisation_by_uid_JSON(self, organisationUid):
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/kataloginformation/organisation/"
            + organisationUid,
            headers=self.headers,
        ).json()
        return r

    # returns:
    # {   'Benamning': {'en': 'EECS/Computer Science', 'sv': 'EECS/Datavetenskap'},
    # 'Giltighetsperiod': {'Startdatum': '2019-01-01', 'link': []},
    # 'Organisationsenhetstyp': 1,
    # 'Organisationskod': 'JH',
    # 'Uid': '2474f616-dc41-11e8-8cc1-eaeeb71b497f',
    # 'link': [   {   'mediaType': 'application/vnd.ladok+xml,application/vnd.ladok-kataloginformation+xml,application/vnd.ladok-kataloginformation+json',
    #                 'method': 'GET',
    #                 'rel': 'self',
    #                 'uri': 'https://api.ladok.se:443/kataloginformation/organisation/2474f616-dc41-11e8-8cc1-eaeeb71b497f'}]}
    # added by GQMJr
    def examen_student_uid_JSON(self, studentUID):
        """
        Returns the student's degree.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url + "examen/internal/student/+studentUID",
            headers=self.headers,
        ).json()
        return r

    # added by GQMJr
    def student_participation_JSON(self, studentUID):
        """
        Returns the student's participation in courses.
        """
        headers = self.headers.copy()
        headers["Content-Type"] = "application/vnd.ladok-studiedeltagande"
        headers["Accept"] += ", application/vnd.ladok-studiedeltagande"
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/studiedeltagande/internal/tillfallesdeltagande"
            + "/kurstillfallesdeltagande/"
            + studentUID,
            headers=self.headers,
        )
        return r.json()

    # added by GQMJr
    def hamtaStudieResultatForStudent_JSON(self, studentUID):
        """
        Returns the study results for a student.
        """
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/resultat/internal/studieresultat/resultat/student/"
            + studentUID,
            headers=self.headers,
        ).json()
        return r

    #################################################################
    ##
    ## private methods
    ##

    def __get_xsrf_token(self):
        return self.xsrf_token

    def get_xsrf_token(self):
        return self.xsrf_token

    # returns None or a LADOK-formated date
    def __validate_date(self, date_raw):
        datregex = re.compile(r"(\d\d)?(\d\d)-?(\d\d)-?(\d\d)")
        dat = datregex.match(date_raw)
        if dat:
            if dat.group(1) == None:  # add 20, ladok3 won't survive till 2100
                return "20" + dat.group(2) + "-" + dat.group(3) + "-" + dat.group(4)
            else:
                return (
                    dat.group(1)
                    + dat.group(2)
                    + "-"
                    + dat.group(3)
                    + "-"
                    + dat.group(4)
                )
        else:
            return None

    def __get_grade_scale_by_id(self, grade_scale_id):
        return next(
            grade_scale
            for grade_scale in self.get_grade_scales()
            if grade_scale.id == grade_scale_id
        )

    def __get_grade_scale_by_code(self, grade_scale_code):
        return next(
            grade_scale
            for grade_scale in self.get_grade_scales()
            if grade_scale.code == grade_scale_code
        )

    def __get_grade_by_id(self, grade_id):
        for grade_scale in self.get_grade_scales():
            for grade in grade_scale.grades():
                if grade.id == grade_id:
                    return grade

        return None

    def __get_student_data(self, person_nr):
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/studentinformation/student/filtrera?limit=2&orderby=EFTERNAMN_ASC&orderby=FORNAMN_ASC&orderby=PERSONNUMMER_ASC&page=1&personnummer="
            + person_nr
            + "&skipCount=false&sprakkod=sv",
            headers=self.headers,
        ).json()["Resultat"]

        if len(r) != 1:
            return None

        r = r[0]
        # from schemas/schemas.ladok.se-studentinformation.xsd
        #   <xs:complexType name="Student">
        #   <xs:complexContent>
        #     <xs:extension base="base:BaseEntitet">
        #       <xs:sequence>
        #         <xs:element name="Avliden" type="xs:boolean"/>
        #         <xs:element minOccurs="0" name="Efternamn" type="xs:string"/>
        #         <xs:element minOccurs="0" name="ExterntUID" type="xs:string"/>
        #         <xs:element name="FelVidEtableringExternt" type="xs:boolean"/>
        #         <xs:element minOccurs="0" name="Fodelsedata" type="xs:string"/>
        #         <xs:element minOccurs="0" name="Fornamn" type="xs:string"/>
        #         <xs:element minOccurs="0" name="KonID" type="xs:int"/>
        #         <xs:element minOccurs="0" name="Personnummer" type="xs:string"/>
        #         <xs:element minOccurs="0" name="Skyddsstatus" type="xs:string"/>
        #         <xs:element minOccurs="0" ref="si:UnikaIdentifierare"/>
        #       </xs:sequence>
        #     </xs:extension>
        #   </xs:complexContent>
        # </xs:complexType>

        return {
            "id": r["Uid"],  # Ladok-ID
            "first_name": r["Fornamn"],
            "last_name": r["Efternamn"],
            "person_nr": r[
                "Personnummer"
            ],  # tolv siffror, utan bindestreck eller plustecken
            "alive": not r["Avliden"],
        }

    # detta är egentligen kurstillfällen, inte kurser (ID-numret är alltså ett ID-nummer för ett kurstillfälle)
    def __get_student_courses(self, student_id):
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/studiedeltagande/tillfallesdeltagande/kurstillfallesdeltagande/student/"
            + student_id,
            headers=self.headers,
        ).json()

        results = []

        for course in r["Tillfallesdeltaganden"]:
            if (
                not course["Nuvarande"]
                or "Utbildningskod" not in course["Utbildningsinformation"]
            ):
                continue

            results.append(
                {
                    "id": course["Uid"],
                    "round_id": course["Utbildningsinformation"][
                        "UtbildningstillfalleUID"
                    ],  # ett Ladok-ID för kursomgången
                    "education_id": course["Utbildningsinformation"][
                        "UtbildningUID"
                    ],  # ett Ladok-ID för något annat som rör kursen
                    "instance_id": course["Utbildningsinformation"][
                        "UtbildningsinstansUID"
                    ],  # ett Ladok-ID för att rapportera in kursresultat
                    "code": course["Utbildningsinformation"][
                        "Utbildningskod"
                    ],  # kurskod KOPPS
                    "name": course["Utbildningsinformation"]["Benamning"]["sv"],
                }
            )

        return results

    def __get_student_course_moments(self, course_round_id, student_id):
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/resultat/kurstillfalle/"
            + str(course_round_id)
            + "/student/"
            + str(student_id)
            + "/moment",
            headers=self.headers,
        ).json()

        return [
            {
                "course_moment_id": moment["UtbildningsinstansUID"],
                "code": moment["Utbildningskod"],
                "education_id": moment["UtbildningUID"],
                "name": moment["Benamning"]["sv"],
            }
            for moment in r["IngaendeMoment"]
        ]

    def __get_student_course_results(self, course_round_id, student_id):
        r = self.session.get(
            url=self.base_gui_proxy_url
            + "/resultat/studieresultat/student/"
            + student_id
            + "/utbildningstillfalle/"
            + course_round_id,
            headers=self.headers,
        ).json()

        return {
            "id": r["Uid"],
            "results": [
                {
                    "education_id": result["UtbildningUID"],
                    "pending": (
                        {
                            "id": result["Arbetsunderlag"]["Uid"],
                            "moment_id": result["Arbetsunderlag"][
                                "UtbildningsinstansUID"
                            ],
                            "grade": self.__get_grade_by_id(
                                result["Arbetsunderlag"]["Betygsgrad"]
                            ),
                            "date": result["Arbetsunderlag"]["Examinationsdatum"],
                            "grade_scale": self.__get_grade_scale_by_id(
                                result["Arbetsunderlag"]["BetygsskalaID"]
                            ),
                            # behövs vid uppdatering av betygsutkast
                            "last_modified": result["Arbetsunderlag"][
                                "SenasteResultatandring"
                            ],
                        }
                        if "Arbetsunderlag" in result
                        else None
                    ),
                    "attested": (
                        {
                            "id": result["SenastAttesteradeResultat"]["Uid"],
                            "moment_id": result["SenastAttesteradeResultat"][
                                "UtbildningsinstansUID"
                            ],
                            "grade": self.__get_grade_by_id(
                                result["SenastAttesteradeResultat"]["Betygsgrad"]
                            ),
                            "date": result["SenastAttesteradeResultat"][
                                "Examinationsdatum"
                            ],
                            "grade_scale": self.__get_grade_scale_by_id(
                                result["SenastAttesteradeResultat"]["BetygsskalaID"]
                            ),
                        }
                        if "SenastAttesteradeResultat" in result
                        else None
                    ),
                }
                for result in r["ResultatPaUtbildningar"]
            ],
        }


class LadokData:
    """Base class for LADOK data"""

    def __init__(self, /, **kwargs):
        pass

    def make_properties(self, kwargs):
        """Turn keywords into private attributes and read-only properties"""
        for attribute in kwargs:
            # private attributes are named on the form _class__attribute
            priv_attr_prefix = f"_{type(self).__name__}__"
            if priv_attr_prefix in attribute:
                priv_attr_name = attribute
                property_name = attribute.replace(priv_attr_prefix, "")
            else:
                priv_attr_name = priv_attr_prefix + attribute
                property_name = attribute

            setattr(self, priv_attr_name, kwargs[attribute])
            if not hasattr(type(self), property_name):
                setattr(
                    type(self),
                    property_name,
                    property(operator.attrgetter(priv_attr_name)),
                )

    def __eq__(self, other):
        if type(self) == type(other):
            return self.__dict__ == other.__dict__
        return False

    def __repr__(self):
        return str(self.json)

    @property
    def json(self):
        """JSON compatible dictionary representation of the object"""
        json_format = self.__dict__.copy()
        for key, value in json_format.items():
            if isinstance(value, LadokData):
                json_format[key] = value.json
        json_format["type"] = type(self).__name__
        return json_format


class LadokDataEncoder(json.JSONEncoder):
    """JSON encoder for LadokData objects.

    Extends JSONEncoder to properly serialize LadokData objects using their
    json property for consistent JSON output.
    """

    def default(self, object):
        """Convert LadokData objects to JSON-serializable format.

        Args:
            object: The object to encode.

        Returns:
            dict: JSON representation for LadokData objects, or default handling.
        """
        if isinstance(object, LadokData):
            return object.json
        return super().default(object)


class LadokRemoteData(LadokData):
    """Base class for remote LADOK data"""

    def __init__(self, /, **kwargs):
        super().__init__(**kwargs)
        if "_LadokRemoteData__ladok" in kwargs:
            self.make_properties(**kwargs)
        else:
            self.__ladok = kwargs.pop("ladok")

    @property
    def ladok(self):
        return self.__ladok

    def pull(self):
        """Pull updates for object from LADOK"""
        raise NotImplementedError("This object doesn't support pulling from LADOK")

    def push(self):
        """Push changes made to the object to LADOK"""
        raise NotImplementedError("This object doesn't support pushing to LADOK")


class GradeScale(LadokData):
    """A grade scale"""

    def __init__(self, /, **kwargs):
        super().__init__(**kwargs)

        if "_GradeScale__id" in kwargs:
            self.make_properties(**kwargs)
        else:
            self.__id = int(kwargs.pop("ID"))
            self.__code = kwargs.pop("Kod")
            self.__name = kwargs.pop("Benamning")["sv"]
            self.__grades = [
                Grade(**grade_data) for grade_data in kwargs.pop("Betygsgrader")
            ]

    @property
    def id(self):
        return self.__id

    @property
    def code(self):
        return self.__code

    @property
    def name(self):
        return self.__name

    def grades(self, /, **kwargs):
        """Returns grades filtered on keyword"""
        return filter_on_keys(self.__grades, **kwargs)

    def __contains__(self, grade):
        return grade in self.__grades

    def __iter__(self):
        return iter(self.__grades)


class Grade(LadokData):
    """An individual grade part of a grade scale"""

    def __init__(self, /, **json_data):
        """Constructor taking a dictionary (JSON-like) structure"""
        if "_Grade__id" in json_data:
            self.make_properties(**json_data)
        else:
            self.__id = int(json_data.pop("ID"))
            self.__code = json_data.pop("Kod")
            self.__accepted = json_data.pop("GiltigSomSlutbetyg")

    @property
    def id(self):
        return self.__id

    @property
    def code(self):
        return self.__code

    def __str__(self):
        return self.code

    @property
    def accepted(self):
        return self.__accepted

    def __eq__(self, other):
        if isinstance(other, Grade):
            return self.__dict__ == other.__dict__
        elif isinstance(other, str):
            return self.code == other
        else:
            raise NotImplementedError(f"can't test equality with {type(other)}")


class Student(LadokRemoteData):
    """Class representing a student and related data"""

    def __init__(self, /, **kwargs):
        """Requires ladok (a LadokSession object),
        id (either a personnummer or LADOK ID)"""
        super().__init__(**kwargs)
        id = kwargs.pop("id")
        self.__personnummer = format_personnummer(id)
        if not self.__personnummer:
            self.__ladok_id = id
        else:
            self.__ladok_id = None

    def pull(self):
        """pull student data from LADOK"""
        self.__get_personal_attributes()
        self.__get_study_attributes()

    def __get_personal_attributes(self):
        """Helper method that fetches personal attributes"""
        if self.__ladok_id:
            record = self.ladok.get_student_data_by_uid_JSON(self.__ladok_id)
        elif self.__personnummer:
            record = self.ladok.get_student_data_JSON(self.__personnummer)
        else:
            raise AttributeError("neither personnummer, nor LADOK ID set")

        self.__ladok_id = record["Uid"]
        self.__personnummer = record["Personnummer"]  # twelve digits only
        self.__first_name = record["Fornamn"]
        self.__last_name = record["Efternamn"]
        self.__alive = not record["Avliden"]

    @property
    def ladok_id(self):
        """Return the student's LADOK ID"""
        try:
            if self.__ladok_id:
                return self.__ladok_id
        except:
            pass
        self.__get_personal_attributes()
        return self.__ladok_id

    @property
    def personnummer(self):
        """Return the student's personnummer"""
        try:
            if self.__personnummer:
                return self.__personnummer
        except:
            pass
        self.__get_personal_attributes()
        return self.__personnummer

    @property
    def first_name(self):
        """Return the student's first name"""
        try:
            return self.__first_name
        except:
            self.__get_personal_attributes()
        return self.__first_name

    @property
    def last_name(self):
        """Return the student's last name"""
        try:
            return self.__last_name
        except:
            self.__get_personal_attributes()
        return self.__last_name

    def __str__(self):
        return f"{self.personnummer} {self.first_name} {self.last_name}"

    @property
    def alive(self):
        """Return whether student is alive or not"""
        try:
            return self.__alive
        except:
            self.__get_personal_attributes()
        return self.__alive

    @property
    def email(self):
        """Return the student's email address"""
        try:
            return self.__email
        except:
            self.__get_contact_attributes()
        return self.__email

    @property
    def phone(self):
        """Return the student's phone number"""
        try:
            return self.__phone
        except:
            self.__get_contact_attributes()
        return self.__phone

    @property
    def address(self):
        """Return the student's postal address as a list of lines"""
        try:
            return self.__address
        except:
            self.__get_contact_attributes()
        return self.__address

    def __get_contact_attributes(self):
        """Helper method that fetches contact attributes"""
        try:
            contact_data = self.ladok.get_student_contact_data_JSON(self.ladok_id)

            # Extract email address
            self.__email = None
            if "Epost" in contact_data and contact_data["Epost"]:
                for email in contact_data["Epost"]:
                    if "Adress" in email:
                        self.__email = email["Adress"]
                        break

            # Extract phone number
            self.__phone = None
            if "Telefon" in contact_data and contact_data["Telefon"]:
                for phone in contact_data["Telefon"]:
                    if "Nummer" in phone:
                        self.__phone = phone["Nummer"]
                        break

            # Extract postal address
            self.__address = []
            if "Postadress" in contact_data and contact_data["Postadress"]:
                addr = contact_data["Postadress"]
                if isinstance(addr, list) and len(addr) > 0:
                    addr = addr[0]
                if isinstance(addr, dict):
                    for field in ["Adressrad1", "Adressrad2", "Adressrad3"]:
                        if field in addr and addr[field]:
                            self.__address.append(addr[field])
                    if (
                        "Postnummer" in addr
                        and addr["Postnummer"]
                        and "Postort" in addr
                        and addr["Postort"]
                    ):
                        self.__address.append(f"{addr['Postnummer']} {addr['Postort']}")

        except Exception:
            # If contact data can't be retrieved, set default empty values
            self.__email = None
            self.__phone = None
            self.__address = []

    @property
    def email(self):
        """Return the student's email address"""
        try:
            return self.__email
        except:
            self.__get_contact_attributes()
        return self.__email

    @property
    def phone(self):
        """Return the student's phone number"""
        try:
            return self.__phone
        except:
            self.__get_contact_attributes()
        return self.__phone

    @property
    def address(self):
        """Return the student's postal address as a list of lines"""
        try:
            return self.__address
        except:
            self.__get_contact_attributes()
        return self.__address

    def __get_contact_attributes(self):
        """Helper method that fetches contact attributes"""
        try:
            contact_data = self.ladok.get_student_contact_data_JSON(self.ladok_id)

            # Extract email address
            self.__email = None
            if "Epost" in contact_data and contact_data["Epost"]:
                for email in contact_data["Epost"]:
                    if "Adress" in email:
                        self.__email = email["Adress"]
                        break

            # Extract phone number
            self.__phone = None
            if "Telefon" in contact_data and contact_data["Telefon"]:
                for phone in contact_data["Telefon"]:
                    if "Nummer" in phone:
                        self.__phone = phone["Nummer"]
                        break

            # Extract postal address
            self.__address = []
            if "Postadress" in contact_data and contact_data["Postadress"]:
                addr = contact_data["Postadress"]
                if isinstance(addr, list) and len(addr) > 0:
                    addr = addr[0]
                if isinstance(addr, dict):
                    for field in ["Adressrad1", "Adressrad2", "Adressrad3"]:
                        if field in addr and addr[field]:
                            self.__address.append(addr[field])
                    if (
                        "Postnummer" in addr
                        and addr["Postnummer"]
                        and "Postort" in addr
                        and addr["Postort"]
                    ):
                        self.__address.append(f"{addr['Postnummer']} {addr['Postort']}")

        except Exception:
            # If contact data can't be retrieved, set default empty values
            self.__email = None
            self.__phone = None
            self.__address = []

    def __get_study_attributes(self):
        """Helper method to fetch study related attributes"""
        self.__courses = []

        for course in self.ladok.registrations_JSON(self.ladok_id):
            if (
                not course["Nuvarande"]
                or "Utbildningskod" not in course["Utbildningsinformation"]
            ):
                continue

            self.__courses.append(
                CourseRegistration(
                    ladok=self.ladok, student=self, **course["Utbildningsinformation"]
                )
            )

    def courses(self, /, **kwargs):
        """
        Returns a list of courses that the student is registered on.
        Filtered based on keywords, see ladok3.filter_on_keys for details.
        """
        try:
            courses = self.__courses
        except:
            self.__get_study_attributes()
            courses = self.__courses

        return filter_on_keys(courses, **kwargs)

    @property
    def suspensions(self):
        """
        The list of the students' suspensions.
        """
        suspensions = self.ladok.get_student_suspensions_JSON(self.ladok_id)[
            "Avstangning"
        ]
        return [Suspension(**suspension) for suspension in suspensions]


class Suspension(LadokData):
    """A suspension"""

    def __init__(self, /, **kwargs):
        super().__init__(**kwargs)
        self.__note = kwargs.pop("Anteckning")
        self.__validity = (
            datetime.date.fromisoformat(kwargs["Giltighetsperiod"]["Startdatum"]),
            datetime.date.fromisoformat(kwargs["Giltighetsperiod"]["Slutdatum"]),
        )

    @property
    def note(self):
        """
        The note of the suspension. This is usually a case number.
        """
        return self.__note

    @property
    def validity(self):
        """
        A tuple (start, end) of the validity period of the suspension.
        """
        return self.__validity

    @property
    def is_current(self):
        """
        Is True if the suspension is currently valid.
        """
        return self.validity[0] <= datetime.date.today() <= self.validity[1]

    def __str__(self):
        return f"{self.validity[0]}--{self.validity[1]}"


class CourseInstance(LadokRemoteData):
    """Represents a course instance. Must be constructed from at least
    ladok (a LadokSession object),
    UtbildningsinstansUID (an instance_id from LADOK),
    optionally a data dictionary from LADOK"""

    def __init__(self, /, **kwargs):
        self.__instance_id = kwargs.pop("UtbildningsinstansUID")
        super().__init__(**kwargs)  # sets self.ladok

        try:
            self.__assign_attr(kwargs)
        except:
            self.__pull_attributes()

    def __assign_attr(self, data):
        self.__components = []
        if "IngaendeMoment" in data:
            self.__components += [
                CourseComponent(ladok=self.ladok, course=self, **component)
                for component in data["IngaendeMoment"]
            ]
        try:
            course_component_data = data.copy()
            course_component_data["ladok"] = self.ladok
            self.__components.append(
                CourseComponent(course=self, **course_component_data)
            )
        except KeyError:
            pass

        self.__name = data.pop("Benamning")
        self.__code = data.pop("Utbildningskod")

        self.__credits = data.pop("Omfattning")
        self.__unit = data.pop("Enhet")

        self.__version = data.pop("Versionsnummer")

        self.__education_id = data.pop("UtbildningUID")

        self.__grade_scale = self.ladok.get_grade_scales(id=data.pop("BetygsskalaID"))

    def __pull_attributes(self):
        data = self.ladok.course_round_components_JSON(self.round_id)
        try:
            self.__assign_attr(data)
        except:
            self.__assign_faux(data)

    def pull(self):
        self.__pull_attributes()

    def __assign_faux(self, data):
        self.__components = []
        if "IngaendeMoment" in data:
            self.__components += [
                CourseComponent(ladok=self.ladok, course=self, **component)
                for component in data["IngaendeMoment"]
            ]
        try:
            course_component_data = data.copy()
            course_component_data["ladok"] = self.ladok
            self.__components.append(
                CourseComponent(course=self, **course_component_data)
            )
        except KeyError:
            pass

        self.__name = data.pop("Benamning", None)
        self.__code = data.pop("Utbildningskod", None)

        self.__credits = data.pop("Omfattning", None)
        self.__unit = data.pop("Enhet", None)

        self.__version = data.pop("Versionsnummer", None)

        self.__education_id = data.pop("UtbildningUID", None)

        try:
            self.__grade_scale = self.ladok.get_grade_scales(
                id=data.pop("BetygsskalaID")
            )
        except KeyError:
            self.__grade_scale = None

    @property
    def instance_id(self):
        return self.__instance_id

    @property
    def education_id(self):
        return self.__education_id

    @property
    def code(self):
        return self.__code

    @property
    def name(self):
        return self.__name["en"]

    @property
    def version(self):
        return self.__version

    @property
    def grade_scale(self):
        return self.__grade_scale

    @property
    def credits(self):
        return self.__credits

    @property
    def unit(self):
        return self.__unit

    def components(self, /, **kwargs):
        """Returns the list of components, filtered on keywords"""
        return filter_on_keys(self.__components, **kwargs)


class CourseRound(CourseInstance):
    """Represents a course round"""

    def __init__(self, /, **kwargs):
        """
        Must be constructed from at least:
        Uid, TillfallesKod, Startdatum, Slutdatum
        """
        self.__round_id = kwargs.pop("Uid")
        self.__round_code = kwargs.pop("TillfallesKod")

        self.__start = datetime.date.fromisoformat(kwargs.pop("Startdatum"))
        self.__end = datetime.date.fromisoformat(kwargs.pop("Slutdatum"))

        instance_data = kwargs.pop("Utbildningsinstans")
        instance_data["UtbildningsinstansUID"] = instance_data.pop("Uid")
        super().__init__(ladok=kwargs.pop("ladok"), **instance_data)

    @property
    def round_id(self):
        return self.__round_id

    @property
    def round_code(self):
        return self.__round_code

    @property
    def start(self):
        return self.__start

    @property
    def end(self):
        return self.__end

    def results(self, /, **kwargs):
        """Returns all students' results on the course"""
        try:
            self.__results
        except:
            self.__fetch_results()

        return filter_on_keys(self.__results, **kwargs)

    def __fetch_results(self):
        raise NotImplementedError(
            f"{type(self).__name__}.__fetch_results not implemented"
        )

    def participants(self, /, **kwargs):
        """Returns a Student object for each participant in the course."""
        try:
            self.__participants
        except:
            self.__fetch_participants()

        return filter_on_keys(self.__participants, **kwargs)

    def __fetch_participants(self):
        self.__participants = []
        for student in self.ladok.participants_JSON(self.round_id):
            self.__participants.append(
                self.ladok.get_student(student["Student"]["Uid"])
            )


class CourseComponent(LadokData):
    """Represents a course component of a course registration"""

    def __init__(self, /, **kwargs):
        super().__init__(**kwargs)

        self.__course = kwargs.pop("course")

        if "UtbildningsinstansUID" in kwargs:
            self.__instance_id = kwargs.pop("UtbildningsinstansUID")
        else:
            self.__instance_id = kwargs.pop("Uid")

        self.__education_id = kwargs.pop("UtbildningUID")

        self.__code = kwargs.pop("Utbildningskod")
        description = kwargs.pop("Benamning")
        if isinstance(description, dict):
            self.__description = description["sv"]
        else:
            self.__description = description

        self.__credits = kwargs.pop("Omfattning", None)
        self.__unit = kwargs.pop("Enhet", None)

        ladok = kwargs.pop("ladok")
        grade_scale_id = kwargs.pop("BetygsskalaID")
        self.__grade_scale = ladok.get_grade_scales(id=grade_scale_id)[0]

    @property
    def course(self):
        return self.__course

    @property
    def instance_id(self):
        return self.__instance_id

    @property
    def education_id(self):
        return self.__education_id

    @property
    def code(self):
        """Returns the name of the component (as in syllabus)"""
        return self.__code

    @property
    def description(self):
        """Returns description of component (as in syllabus)"""
        return self.__description

    @property
    def unit(self):
        """Returns the unit for the credits"""
        return self.__unit

    @property
    def credits(self):
        """Returns the number of credits"""
        return self.__credits

    @property
    def grade_scale(self):
        return self.__grade_scale

    def __str__(self):
        return self.code

    def __eq__(self, other):
        if isinstance(other, str):
            return self.code == other
        return self.__dict__ == other.__dict__


class CourseRegistration(CourseInstance):
    """Represents a student's participation in a course instance"""

    def __init__(self, /, **kwargs):
        self.__student = kwargs.pop("student")

        # ett Ladok-ID för kursomgången
        self.__round_id = kwargs.pop("UtbildningstillfalleUID")
        self.__round_code = kwargs.pop("Utbildningstillfalleskod", None)

        dates = kwargs.pop("Studieperiod")
        self.__start = datetime.date.fromisoformat(dates["Startdatum"])
        self.__end = datetime.date.fromisoformat(dates["Slutdatum"])

        super().__init__(**kwargs)

    @property
    def round_id(self):
        """Returns LADOK ID for the course round (kursomgång)"""
        return self.__round_id

    @property
    def round_code(self):
        """Returns the human-readable round code (tillfälleskod)"""
        return self.__round_code

    @property
    def start(self):
        return self.__start

    @property
    def end(self):
        return self.__end

    def __str__(self):
        return f"{self.code} {self.round_code or ''} ({self.start}--{self.end})"

    def __repr__(self):
        return f"{self.code}:{self.round_code or ''}:{self.start}--{self.end}"

    def results(self, /, **kwargs):
        """Returns the student's results on the course, filtered on keywords"""
        try:
            return filter_on_keys(self.__results, **kwargs)
        except:
            self.__fill_results()
        return filter_on_keys(self.__results, **kwargs)

    def __fill_results(self):
        """Helper method to fetch results from LADOK"""
        response = self.ladok.student_results_JSON(
            self.__student.ladok_id, self.education_id
        )["Kursversioner"][0]

        self.__results = []

        for result in response["VersionensModuler"]:
            try:
                self.__results.append(
                    CourseResult(
                        ladok=self.ladok,
                        components=self.components(),
                        student=self.__student,
                        **result,
                    )
                )
            except TypeError:
                pass
        try:
            self.__results.append(
                CourseResult(
                    ladok=self.ladok,
                    components=self.components(),
                    student=self.__student,
                    **response["VersionensKurs"],
                )
            )
        except TypeError:
            pass
        for component in self.components():
            if not list(filter_on_keys(self.__results, component=component.code)):
                self.__results.append(
                    CourseResult(
                        ladok=self.ladok, component=component, student=self.__student
                    )
                )

    def push(self):
        """Pushes any new results"""
        for result in self.results():
            result.push()


class CourseResult(LadokRemoteData):
    """Represents a result on a course module"""

    def __init__(self, /, **kwargs):
        """To construct this object we must give existing data, i.e.
        Arbetsunderlag or SenastAttesteradeResultat directly from LADOK."""
        super().__init__(**kwargs)

        self.__student = kwargs.pop("student")

        self.__attested = False
        if "component" in kwargs:
            self.__component = kwargs.pop("component")
            self.__populate_attributes()
        elif "components" in kwargs and "ResultatPaUtbildning" in kwargs:
            components = kwargs.pop("components")

            results = kwargs.pop("ResultatPaUtbildning")

            if "Arbetsunderlag" in results:
                data = results["Arbetsunderlag"]
            elif "SenastAttesteradeResultat" in results:
                self.__attested = True
                data = results["SenastAttesteradeResultat"]
            else:
                data = kwargs

            self.__populate_attributes(**data, components=components)
        else:
            raise TypeError("not enough keys given to construct object")

    def __populate_attributes(self, /, **data):
        if not data:
            self.__uid = None
            self.__instance_id = self.__component.instance_id

            self.__date = None
            self.__grade_scale = self.__component.grade_scale
            self.__grade = None

            self.__modified = False
            self.__last_modified = None
        else:
            self.__uid = data.pop("Uid", None)
            self.__instance_id = data.pop("UtbildningsinstansUID")
            self.__results_id = data.pop("ResultatUID", None)
            self.__study_results_id = data.pop("StudieresultatUID", None)

            try:
                grade = data.pop("Betygsgrad", None)
                grade_scale_id = data.pop("BetygsskalaID")
            except KeyError:
                grade_scale_id = int(data["Betygsskala"]["ID"])

            self.__date = data.pop("Examinationsdatum", None)
            self.__grade_scale = self.ladok.get_grade_scales(id=grade_scale_id)[0]
            if grade:
                self.__grade = self.__grade_scale.grades(id=grade)[0]
            else:
                self.__grade = None

            if "components" in data:
                components = data.pop("components")
                component_list = filter_on_keys(
                    components, instance_id=self.__instance_id
                )
                self.__component = component_list[0] if component_list else None

            self.__last_modified = data.pop("SenasteResultatandring", None)
            self.__modified = False

    @property
    def component(self):
        """Returns the component the results is for"""
        return self.__component

    @property
    def grade_scale(self):
        """Returns the grade scale for the component"""
        return self.__grade_scale

    @property
    def grade(self):
        """Returns the grade set for the component"""
        return self.__grade

    def set_grade(self, grade, date):
        """Sets a new grade and date for the component"""
        if self.attested:
            raise AttributeError("can't change already attested grade")

        if isinstance(grade, Grade) and grade not in self.grade_scale.grades():
            raise TypeError(
                f"The grade {grade} is not in" f"the scale {self.grade_scale.code}"
            )
        elif isinstance(grade, str):
            try:
                grade = self.grade_scale.grades(code=grade)[0]
            except:
                raise TypeError(
                    f"The grade {grade} is not in the scale {self.grade_scale.code}"
                )
        else:
            raise TypeError(f"Can't use type {type(grade)} for grade")

        if isinstance(date, str):
            date = datetime.date.fromisoformat(date)
        elif not isinstance(date, datetime.date):
            raise TypeError(f"Type {type(date)} not supported for date")

        self.__grade = grade
        self.__date = date

        self.__modified = True
        self.push()

    def finalize(self, graders=[], notify=False):
        """Finalizes the set grade"""
        if self.modified:
            self.push()

        reporter_id = self.ladok.user_info_JSON()["AnvandareUID"]

        if notify:
            response = self.ladok.finalize_result_JSON(
                self.__results_id,
                self.__last_modified,
                reporter_id,
                reporter_id,
                others=graders,
            )
        else:
            response = self.ladok.finalize_result_JSON(
                self.__results_id, self.__last_modified, reporter_id, others=graders
            )

        self.__populate_attributes(**response)

    @property
    def modified(self):
        """Returns True if there are unpushed changes"""
        return self.__modified

    @property
    def date(self):
        """Returns the date of the grade"""
        return self.__date

    @property
    def attested(self):
        """Returns True if the grade has been attested in LADOK"""
        return self.__attested

    def __str__(self):
        return (
            f"{self.component} {self.grade} "
            f"{self.date}{'*' if not self.attested else ''}"
        )

    def push(self):
        if self.__uid:
            try:
                response = self.ladok.update_result_JSON(
                    self.__uid,
                    self.grade.id,
                    self.date.isoformat(),
                    self.__last_modified,
                )
            except Exception as err:
                raise LadokError(
                    f"couldn't update {self.component.code} to {self.grade} ({self.date})"
                    f" to LADOK: {err}"
                )

            self.__populate_attributes(**response)
        else:
            try:
                response = self.ladok.create_result_JSON(
                    self.__student.ladok_id,
                    self.__component.course.instance_id,
                    self.__component.instance_id,
                    self.grade.id,
                    self.date.isoformat(),
                )
            except Exception as err:
                raise LadokError(
                    "Couldn't register "
                    f"{self.component} {self.grade} {self.date}: {err}"
                )

            self.__populate_attributes(**response)
        self.__modified = False


class LadokError(Exception):
    """
    Base exception class for all LADOK-related errors.

    This is the parent class for all LADOK-specific exceptions. It can be used
    to catch any LADOK-related error in a single exception handler while still
    allowing more specific error handling when needed.

    All other LADOK exception classes inherit from this class, ensuring
    backward compatibility with existing code that catches generic exceptions.
    """

    pass


class LadokServerError(LadokError):
    """
    Exception for server-side LADOK errors.

    This exception is raised when the LADOK server returns an error response,
    typically containing an error message in the response JSON under the
    "Meddelande" key. This indicates that the request reached the server
    successfully, but the server was unable to process it due to business
    logic constraints or data validation issues on the server side.

    Examples:
    - Attempting to register a grade for a student not enrolled in the course
    - Trying to access data that the authenticated user doesn't have permission to view
    - Server-side validation failures
    """

    pass


class LadokValidationError(LadokError):
    """
    Exception for data validation errors.

    This exception is raised when input data fails validation before being
    sent to the LADOK API. This includes format validation, business rule
    validation, and other client-side checks that can be performed without
    contacting the server.

    Examples:
    - Invalid Swedish personal numbers (personnummer)
    - Invalid grade values for a specific grading scale
    - Missing required fields
    - Date format errors
    """

    pass


class LadokAPIError(LadokError):
    """
    Exception for API/HTTP related errors.

    This exception is raised when there are problems with the HTTP communication
    to the LADOK API or when the API returns unexpected responses. This includes
    network connectivity issues, HTTP protocol errors, and malformed responses.

    Examples:
    - Network connectivity failures
    - HTTP status codes indicating client or server errors
    - Malformed JSON responses
    - Authentication failures
    - Timeouts
    """

    pass


class LadokNotFoundError(LadokError):
    """
    Exception for resource not found errors.

    This exception is raised when a requested resource cannot be found in LADOK.
    This is typically used for HTTP 404 responses or when searching for entities
    that don't exist.

    Examples:
    - Course instances that don't exist
    - Students not found in the system
    - Course components that are not part of a course
    - Non-existent course rounds
    """

    pass


def filter_on_keys(items, /, **kwargs):
    """
    Input:
    - items is a list of objects.
    - kwargs is a dictionary where keys match the attributes of the objects in
      items.

    Output:
    - Only objects where *all* key--value pairs match for the corresponding
      attribues.
    - If values are strings, the value from kwargs is interpreted as a regular
      expression.

    Example:
    student.first_name = "Student"
    student.last_name = "Studentdotter"

    filter_on_keys([student], firt_name="Student")
      gives [student]
    filter_on_keys([student], firt_name="Student", last_name="Studentsson")
      gives []
    """
    for key in kwargs:
        items = filter(
            lambda x: compare_values(operator.attrgetter(key)(x), kwargs[key]), items
        )
    return list(items)


def filter_on_any_key(items, /, **kwargs):
    """
    Input:
    - items is a list of objects.
    - kwargs is a dictionary where keys match the attributes of the objects in
      items.

    Output:
    - Only objects where *any* key--value pairs match for the corresponding
      attribues.
    - If values are strings, the value from kwargs is interpreted as a regular
      expression.

    Example:
    student.first_name = "Student"
    student.last_name = "Studentsdotter"

    filter_on_keys([student], firt_name="Student")
      gives [student]
    filter_on_keys([student], firt_name="Student", last_name="Studentsson")
      gives [student]
    """
    matching_items = []
    for item in items:
        for key in kwargs:
            if compare_values(operator.attrgetter(key)(item), kwargs[key]):
                matching_items.append(item)
                break

    return matching_items


def compare_values(val1, val2):
    """
    Compares val1 and val2:
    - if val1 and val2 both are strings, then val2 is interpreted as a regular
      expression.
    - otherwise we use ==
    """
    if isinstance(val1, str) and isinstance(val2, str):
        return re.search(val2, val1)

    return val1 == val2


def get_translation(lang_code, list_of_translations):
    for translation in list_of_translations:
        if translation["Sprakkod"] == lang_code:
            return translation["Text"]
    raise KeyError(f"no translation for language {lang_code}")


def format_personnummer(person_nr_raw):
    """Returns None or a LADOK-formated person nr"""
    pnrregex = re.compile(r"^(\d\d)?(\d\d)(\d\d\d\d)[+\-]?(\w\w\w\w)$")
    pnr = pnrregex.match(person_nr_raw)
    if pnr:
        now = datetime.datetime.now()
        if pnr.group(1) == None:  # first digits 19 or 20 missing
            if now.year - 2000 >= int(pnr.group(2)) + 5:  # must be > 5 years old
                return "20" + pnr.group(2) + pnr.group(3) + pnr.group(4)
            else:
                return "19" + pnr.group(2) + pnr.group(3) + pnr.group(4)
        else:
            return pnr.group(1) + pnr.group(2) + pnr.group(3) + pnr.group(4)
    else:
        return None


def clean_data(json_obj):
    """
    Clean a JSON object by removing internal links and pseudonymizing personal data.

    Args:
        json_obj (dict or list): The JSON data to clean.

    Returns:
        dict or list: The cleaned JSON object.
    """
    remove_links(json_obj)
    pseudonymize(json_obj)
    return json_obj


def remove_links(json_obj):
    """
    Recursively removes all "link" keys and values
    """
    if isinstance(json_obj, dict):
        if "link" in json_obj:
            json_obj.pop("link")
        for key, value in json_obj.items():
            remove_links(value)
    elif isinstance(json_obj, list):
        for item in json_obj:
            remove_links(item)


def pseudonymize(json_obj):
    """
    Recursively pseudonymizes a JSON data record
    """
    if isinstance(json_obj, dict):
        if "Fornamn" in json_obj:
            json_obj["Fornamn"] = "Student"
        if "Efternamn" in json_obj:
            json_obj["Efternamn"] = "Studentzadeh"
        if "Personnummer" in json_obj:
            json_obj["Personnummer"] = "191234561234"
        if "Epostadress" in json_obj:
            json_obj["Epostadress"] = "user@domain.se"
        if "Anvandarnamn" in json_obj:
            json_obj["Anvandarnamn"] = "user@domain.se"
        if "Utdelningsadress" in json_obj:
            json_obj["Utdelningsadress"] = "Stora vägen 1"
        if "Postnummer" in json_obj:
            json_obj["Postnummer"] = "12345"
        if "Postort" in json_obj:
            json_obj["Postort"] = "Byn"
        if "Telefonnummer" in json_obj:
            json_obj["Telefonnummer"] = "0701234567"
        for value in json_obj.values():
            pseudonymize(value)
    elif isinstance(json_obj, list):
        for item in json_obj:
            pseudonymize(item)
