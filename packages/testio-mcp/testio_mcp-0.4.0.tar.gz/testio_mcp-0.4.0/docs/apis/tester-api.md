# Tester API v1 Documentation

## Overview

This is a comprehensive REST API for managing testing workflows, bugs, test cycles, and tester management. The API uses token-based authentication and returns JSON responses.

**Base URL:** `http://api.127.0.0.1.xip.io/tester/v1`

**Authentication:** Bearer token in `Authorization` header

---

## Resource Groups

### AccessTokens

#### Create Doorkeeper Token
- **Endpoint:** `POST /access_tokens`
- **Auth:** Required
- **Request Body:**
  ```json
  {
    "client_id": "string (UUID)",
    "purpose": "string"
  }
  ```
- **Response:** `201 Created`
  ```json
  {
    "token": "string"
  }
  ```

---

### Achievements

#### Send Badge
- **Endpoint:** `POST /achievements`
- **Auth:** Required
- **Request Body:**
  ```json
  {
    "test_cycle_id": "integer",
    "achievement": {
      "grantee_id": "integer (required)",
      "comment": "string (required)",
      "badge_id": "integer (required)"
    }
  }
  ```
- **Response:** `201 Created`
  ```json
  {
    "status": 201
  }
  ```

---

### Attachments

#### Create Attachment
- **Endpoint:** `POST /attachments`
- **Auth:** Required
- **Content-Type:** `multipart/form-data`
- **Request Fields:**
  - `file`: Binary file (required)
  - `type`: String (e.g., "test_case_step")
- **Response:** `201 Created`
  ```json
  {
    "attachment": {
      "id": "integer",
      "content_type": "string",
      "file_type": "string",
      "file_size": "integer",
      "url": "string",
      "thumbnail_urls": {
        "50x50": "string",
        "150x150": "string",
        "200x200": "string",
        "x250": "string",
        "50x36": "string"
      },
      "uuid": "string"
    }
  }
  ```

---

### Badges

#### Get Available Badges
- **Endpoint:** `GET /badges`
- **Auth:** Required
- **Query Parameters:**
  - `test_cycle_id`: integer
  - `grantee_id`: integer (required)
- **Response:** `200 OK`
  ```json
  {
    "grantee": {
      "id": "integer",
      "screenname": "string",
      "avatar_url": "string",
      "level": "string or null"
    },
    "badges": [
      {
        "id": "integer",
        "name": "string",
        "image_url": "string"
      }
    ]
  }
  ```

#### Get Single Badge
- **Endpoint:** `GET /badges/:badge_id`
- **Auth:** Required
- **Path Parameters:**
  - `badge_id`: integer (required)
- **Query Parameters:**
  - `grantee_id`: integer
- **Response:** `200 OK`
  ```json
  {
    "badge": {
      "id": "integer",
      "name": "string",
      "image_url": "string",
      "comments": [
        {
          "author": "string",
          "body": "string",
          "image_url": "string",
          "created_at": "timestamp"
        }
      ]
    }
  }
  ```

---

### Bills

#### Get Billing Info
- **Endpoint:** `GET /billing_info`
- **Auth:** Required
- **Response:** `200 OK`
  ```json
  {
    "billing_info": {
      "amount": "string",
      "status": "string",
      "description": "string",
      "cirro_url": "string",
      "bills": [
        {
          "id": "integer",
          "amount": "string",
          "status": "string",
          "title": "string",
          "activity": {
            "created_at": "timestamp",
            "tester_invitation_id": "integer",
            "test_cycle": {
              "id": "integer",
              "category": "string"
            }
          }
        }
      ]
    }
  }
  ```

---

### Bugs

#### Create Bug
- **Endpoint:** `POST /bugs`
- **Auth:** Required
- **Request Body:**
  ```json
  {
    "bug": {
      "title": "string",
      "expected_result": "string",
      "actual_result": "string",
      "steps": ["string"]
    }
  }
  ```
- **Response:** `201 Created`

#### Get Bug
- **Endpoint:** `GET /bugs/:bug_id`
- **Auth:** Required
- **Path Parameters:**
  - `bug_id`: integer (required)
- **Query Parameters:**
  - `included`: string (e.g., "bug" for fresher bug type)
- **Response:** `200 OK` - Returns full bug object with metadata

#### Get Bug List
- **Endpoint:** `GET /bugs`
- **Auth:** Required
- **Query Parameters:**
  - `per_page`: integer
  - `page`: integer
- **Response:** `200 OK` - Returns array of bug objects

#### Update Bug
- **Endpoint:** `PUT /bugs/:bug_id`
- **Auth:** Required
- **Path Parameters:**
  - `bug_id`: integer (required)

#### Delete Bug
- **Endpoint:** `DELETE /bugs/:bug_id`
- **Auth:** Required
- **Path Parameters:**
  - `bug_id`: integer (required)

#### Get Bug Permissions
- **Endpoint:** `GET /bugs/:bug_id/permissions`
- **Auth:** Required

#### Get Bug Types
- **Endpoint:** `GET /bugs/types` or `GET /bug_types`
- **Auth:** Required
- **Response:** `200 OK` - Returns available bug type options

#### Get Known Bugs
- **Endpoint:** `GET /bugs/known`
- **Auth:** Required
- **Response:** `200 OK` - Returns array of known bugs

#### Get Filter Options
- **Endpoint:** `GET /bugs/filter_options`
- **Auth:** Required
- **Response:** `200 OK` - Returns filterable fields and values

#### Post Similar Bugs
- **Endpoint:** `POST /bugs/similar`
- **Auth:** Required
- **Request Body:** Bug query criteria

---

### Bug Comments

#### Create Comment
- **Endpoint:** `POST /bugs/:bug_id/bug_comments`
- **Auth:** Required
- **Path Parameters:**
  - `bug_id`: integer (required)
- **Request Body:**
  ```json
  {
    "bug_comment": {
      "body": "string (required)"
    }
  }
  ```
- **Response:** `201 Created`
  ```json
  {
    "bug_comment": {
      "id": "integer",
      "author": {
        "name": "string",
        "avatar_url": "string"
      },
      "body": "string",
      "created_at": "timestamp"
    }
  }
  ```

#### Get Bug Comments
- **Endpoint:** `GET /bugs/:bug_id/bug_comments`
- **Auth:** Required
- **Path Parameters:**
  - `bug_id`: integer (required)
- **Response:** `200 OK` - Returns array of comment objects

---

### Bug Disputes

#### Create Dispute
- **Endpoint:** `POST /bugs/:bug_id/bug_disputes`
- **Auth:** Required
- **Path Parameters:**
  - `bug_id`: integer (required)
- **Request Body:**
  ```json
  {
    "bug_dispute": {
      "request_message": "string (required)"
    }
  }
  ```
- **Response:** `201 Created`
  ```json
  {
    "bug_dispute": {
      "id": "integer",
      "status": "string (submitted|accepted|rejected)",
      "request": {
        "message": "string",
        "description": "string"
      },
      "response": {
        "message": "string or null",
        "description": "string"
      },
      "created_at": "timestamp",
      "accepted_at": "timestamp or null",
      "rejected_at": "timestamp or null"
    }
  }
  ```

---

### Bug Fix Confirmations

#### Get Available Confirmations
- **Endpoint:** `GET /bug_fix_confirmations/available`
- **Auth:** Required
- **Query Parameters:**
  - `per_page`: integer
  - `page`: integer
  - `included`: string (e.g., "bug")
- **Response:** `200 OK` - Returns array of confirmation objects

#### Start Confirmation
- **Endpoint:** `POST /bug_fix_confirmations/:bug_fix_confirmation_id/bug_fix_confirmation_executions`
- **Auth:** Required
- **Path Parameters:**
  - `bug_fix_confirmation_id`: integer (required)
- **Response:** `201 Created`

#### Get Execution
- **Endpoint:** `GET /bug_fix_confirmation_executions/:bug_fix_confirmation_execution_id`
- **Auth:** Required
- **Path Parameters:**
  - `bug_fix_confirmation_execution_id`: integer (required)
- **Response:** `200 OK`

#### Submit Execution
- **Endpoint:** `PUT /bug_fix_confirmation_executions/:bug_fix_confirmation_execution_id/submit`
- **Auth:** Required
- **Path Parameters:**
  - `bug_fix_confirmation_execution_id`: integer (required)
- **Request Body:**
  ```json
  {
    "execution": {
      "device_configuration": {
        "id": "integer (required)",
        "browsers": [
          {
            "id": "integer"
          }
        ]
      },
      "comment": "string",
      "attachments": [
        {
          "id": "integer"
        }
      ],
      "status_event": "string (required - pass|fail)"
    }
  }
  ```
- **Response:** `200 OK`

#### Cancel Execution
- **Endpoint:** `PUT /bug_fix_confirmation_executions/:bug_fix_confirmation_execution_id/cancel`
- **Auth:** Required
- **Response:** `200 OK`

#### Expire Execution
- **Endpoint:** `PUT /bug_fix_confirmation_executions/:bug_fix_confirmation_execution_id/expire`
- **Auth:** Required
- **Response:** `200 OK`

---

### Bug Report Confirmations

#### Get Confirmation Details
- **Endpoint:** `GET /bug_report_confirmations/:bug_report_confirmation_id`
- **Auth:** Required
- **Path Parameters:**
  - `bug_report_confirmation_id`: integer (required)
- **Response:** `200 OK`

#### Start Confirmation
- **Endpoint:** `POST /bug_report_confirmations/:bug_report_confirmation_id/bug_report_confirmation_executions`
- **Auth:** Required
- **Path Parameters:**
  - `bug_report_confirmation_id`: integer (required)
- **Response:** `201 Created`

#### Get Execution
- **Endpoint:** `GET /bug_report_confirmation_executions/:bug_report_confirmation_execution_id`
- **Auth:** Required
- **Response:** `200 OK`

#### Submit Execution
- **Endpoint:** `PUT /bug_report_confirmation_executions/:bug_report_confirmation_execution_id/submit`
- **Auth:** Required
- **Request Body:**
  ```json
  {
    "bug_report_confirmation_execution": {
      "status_event": "string (required - pass|fail|block)",
      "comment": "string (required)",
      "device_configuration": {
        "id": "integer (required)",
        "browsers": [
          {
            "id": "integer"
          }
        ]
      },
      "attachments": [
        {
          "id": "integer"
        }
      ],
      "screen_size": "string",
      "browser_version": "string",
      "answer": "string"
    }
  }
  ```
- **Response:** `200 OK`

#### Cancel Execution
- **Endpoint:** `PUT /bug_report_confirmation_executions/:bug_report_confirmation_execution_id/cancel`
- **Auth:** Required
- **Response:** `200 OK`

---

### Bug Reproductions

#### Create Reproduction
- **Endpoint:** `POST /bugs/:bug_id/reproduce`
- **Auth:** Required
- **Path Parameters:**
  - `bug_id`: integer (required)
- **Request Body:**
  ```json
  {
    "reproduction": {
      "positive": "boolean",
      "device_configuration": {
        "id": "integer",
        "browsers": [
          {
            "id": "integer"
          }
        ]
      },
      "attachments": [
        {
          "file_name": "string",
          "file_base64": "string"
        }
      ]
    }
  }
  ```
- **Response:** `201 Created`

#### Get Reproduction Info
- **Endpoint:** `GET /bugs/:bug_id/reproduction_info`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Reproduction
- **Endpoint:** `GET /bug_reproductions/:bug_reproduction_id`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Reproductions Needing Work
- **Endpoint:** `GET /bug_reproductions/needing_reproduction`
- **Auth:** Required
- **Query Parameters:**
  - `per_page`: integer
  - `page`: integer
- **Response:** `200 OK`

---

### Bug Reproduction Invitations

#### Get Pending Invitations
- **Endpoint:** `GET /bug_reproduction_invitations/needing_reproduction`
- **Auth:** Required
- **Query Parameters:**
  - `per_page`: integer
  - `page`: integer
  - `included`: string (e.g., "bug")
- **Response:** `200 OK`

#### Get Single Invitation
- **Endpoint:** `GET /bug_reproduction_invitations/:id`
- **Auth:** Required
- **Path Parameters:**
  - `id`: integer (required)
- **Query Parameters:**
  - `included`: string (e.g., "bug")
- **Response:** `200 OK`

#### Accept Invitation
- **Endpoint:** `PUT /bug_reproduction_invitations/:id/accept`
- **Auth:** Required
- **Path Parameters:**
  - `id`: integer (required)
- **Query Parameters:**
  - `included`: string (e.g., "bug")
- **Response:** `200 OK`

#### Decline Invitation
- **Endpoint:** `PUT /bug_reproduction_invitations/:id/decline`
- **Auth:** Required
- **Response:** `200 OK`

#### Reset Accepted Invitation
- **Endpoint:** `PUT /bug_reproduction_invitations/:id/reset`
- **Auth:** Required
- **Response:** `200 OK`

---

### Campaigns

#### Get Campaign
- **Endpoint:** `GET /campaigns/:campaign_id`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Campaigns
- **Endpoint:** `GET /campaigns`
- **Auth:** Required
- **Response:** `200 OK`

---

### Chat Messages

#### Create Message
- **Endpoint:** `POST /chat_messages`
- **Auth:** Required
- **Request Body:** Message content
- **Response:** `201 Created`

#### Get Messages
- **Endpoint:** `GET /chat_messages`
- **Auth:** Required
- **Query Parameters:**
  - `page`: integer
  - `per_page`: integer
- **Response:** `200 OK`

#### Get Announcement Messages
- **Endpoint:** `GET /chat_messages/announcements`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Message Likes
- **Endpoint:** `GET /chat_messages/:message_id/likes`
- **Auth:** Required
- **Response:** `200 OK`

#### Like Message
- **Endpoint:** `POST /chat_messages/:message_id/like`
- **Auth:** Required
- **Response:** `201 Created`

#### Unlike Message
- **Endpoint:** `DELETE /chat_messages/:message_id/like`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Recipients
- **Endpoint:** `GET /chat_messages/recipients`
- **Auth:** Required
- **Response:** `200 OK`

---

### Courses

#### Get Course Summary
- **Endpoint:** `GET /courses/summary`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Courses
- **Endpoint:** `GET /courses`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Course Page
- **Endpoint:** `GET /course_pages/:course_page_id`
- **Auth:** Required
- **Response:** `200 OK`

#### Update Course Page Interaction
- **Endpoint:** `PUT /course_pages/:course_page_id/interactions`
- **Auth:** Required
- **Response:** `200 OK`

#### Restart Course
- **Endpoint:** `POST /courses/:course_id/restart`
- **Auth:** Required
- **Response:** `201 Created`

---

### Custom Reports

#### Create Report
- **Endpoint:** `POST /custom_reports`
- **Auth:** Required
- **Request Body:** Report configuration
- **Response:** `201 Created`

#### Get Report Fields
- **Endpoint:** `GET /custom_reports/fields`
- **Auth:** Required
- **Response:** `200 OK`

---

### Device Configurations

#### Create Configuration
- **Endpoint:** `POST /device_configurations`
- **Auth:** Required
- **Request Body:** Device config details
- **Response:** `201 Created`

#### Retrieve Configuration
- **Endpoint:** `GET /device_configurations/:device_configuration_id`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Tester's Configurations
- **Endpoint:** `GET /device_configurations`
- **Auth:** Required
- **Response:** `200 OK`

#### Update Configuration
- **Endpoint:** `PUT /device_configurations/:device_configuration_id`
- **Auth:** Required
- **Response:** `200 OK`

---

### Devices

#### Search Devices
- **Endpoint:** `GET /devices/search`
- **Auth:** Required
- **Query Parameters:**
  - `keyword`: string
- **Response:** `200 OK`

#### Guess Device
- **Endpoint:** `POST /devices/guess`
- **Auth:** Required
- **Response:** `200 OK`

---

### Feedbacks

#### Create Feedback
- **Endpoint:** `POST /feedbacks`
- **Auth:** Required
- **Request Body:** Feedback content
- **Response:** `201 Created`

#### Get Feedback Fields
- **Endpoint:** `GET /feedbacks/fields`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Test Feedback
- **Endpoint:** `GET /feedbacks/:test_id`
- **Auth:** Required
- **Response:** `200 OK`

#### Update Feedback
- **Endpoint:** `PUT /feedbacks/:feedback_id`
- **Auth:** Required
- **Response:** `200 OK`

---

### Improvement Suggestions

#### Create Suggestion
- **Endpoint:** `POST /improvement_suggestions`
- **Auth:** Required
- **Request Body:** Suggestion details
- **Response:** `201 Created`

#### Get Suggestion Fields
- **Endpoint:** `GET /improvement_suggestions/fields`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Suggestions
- **Endpoint:** `GET /improvement_suggestions`
- **Auth:** Required
- **Response:** `200 OK`

#### React to Suggestion
- **Endpoint:** `POST /improvement_suggestions/:suggestion_id/reactions`
- **Auth:** Required
- **Response:** `201 Created`

#### Update Suggestion
- **Endpoint:** `PUT /improvement_suggestions/:suggestion_id`
- **Auth:** Required
- **Response:** `200 OK`

---

### Me / Current User

#### Get Current User Info
- **Endpoint:** `GET /me`
- **Auth:** Required
- **Response:** `200 OK` - Returns tester profile object

#### Get Tester Permissions
- **Endpoint:** `GET /me/permissions`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Tester State
- **Endpoint:** `GET /me/state`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Intercom Details
- **Endpoint:** `GET /me/intercom_details`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Level Info
- **Endpoint:** `GET /level_info`
- **Auth:** Required
- **Response:** `200 OK`

---

### Notifications

#### Get Parameters
- **Endpoint:** `GET /notifications/parameters`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Schedule
- **Endpoint:** `GET /notifications/schedule`
- **Auth:** Required
- **Response:** `200 OK`

#### Update Parameters
- **Endpoint:** `PUT /notifications/parameters`
- **Auth:** Required
- **Request Body:** Parameter updates
- **Response:** `200 OK`

#### Update Schedule
- **Endpoint:** `PUT /notifications/schedule`
- **Auth:** Required
- **Request Body:** Schedule updates
- **Response:** `200 OK`

---

### OAuth

#### Get API Token
- **Endpoint:** `GET /oauth/token`
- **Auth:** Required
- **Response:** `200 OK`

---

### Operating Systems

#### Get OS with Browsers
- **Endpoint:** `GET /operating_systems`
- **Auth:** Required
- **Response:** `200 OK` - Returns OS list with versions and browsers

---

### Opportunity Invitations

#### Get Invitations
- **Endpoint:** `GET /opportunity_invitations`
- **Auth:** Required
- **Response:** `200 OK`

#### Reject Invitation
- **Endpoint:** `PUT /opportunity_invitations/:invitation_id/reject`
- **Auth:** Required
- **Response:** `200 OK`

---

### Prompt Inputs

#### Create Input
- **Endpoint:** `POST /prompt_inputs`
- **Auth:** Required
- **Request Body:** Prompt content
- **Response:** `201 Created`

---

### Prompt Outputs

#### Get Output
- **Endpoint:** `GET /prompt_outputs/:prompt_output_id`
- **Auth:** Required
- **Response:** `200 OK`

#### React to Output
- **Endpoint:** `POST /prompt_outputs/:prompt_output_id/reactions`
- **Auth:** Required
- **Response:** `201 Created`

---

### Pusher Auth

#### Authorize Presence Channel
- **Endpoint:** `POST /pusher/auth`
- **Auth:** Required
- **Request Body:** Channel subscription data
- **Response:** `200 OK`

---

### Referrals

#### Get Referral Info
- **Endpoint:** `GET /referrals/info`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Leaderboard
- **Endpoint:** `GET /referrals/leaderboard`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Referred Testers
- **Endpoint:** `GET /referrals/referred_testers`
- **Auth:** Required
- **Response:** `200 OK`

#### Redeem Points
- **Endpoint:** `POST /referrals/redeem`
- **Auth:** Required
- **Request Body:** Redemption details
- **Response:** `201 Created`

---

### Registered Devices

#### Create Device
- **Endpoint:** `POST /registered_devices`
- **Auth:** Required
- **Request Body:** Device info
- **Response:** `201 Created`

#### Get Devices
- **Endpoint:** `GET /registered_devices`
- **Auth:** Required
- **Response:** `200 OK`

---

### Single Jobs

#### Get Filters
- **Endpoint:** `GET /single_jobs/filters`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Job List
- **Endpoint:** `GET /single_jobs`
- **Auth:** Required
- **Query Parameters:**
  - `page`: integer
  - `per_page`: integer
- **Response:** `200 OK`

---

### Test Case Bugs

#### Create Bug
- **Endpoint:** `POST /test_cases/:test_case_id/bugs`
- **Auth:** Required
- **Response:** `201 Created`

#### Update Bug
- **Endpoint:** `PUT /test_cases/:test_case_id/bugs/:bug_id`
- **Auth:** Required
- **Response:** `200 OK`

#### Delete Bug
- **Endpoint:** `DELETE /test_cases/:test_case_id/bugs/:bug_id`
- **Auth:** Required
- **Response:** `200 OK`

---

### Test Case Executions

#### Create Execution
- **Endpoint:** `POST /test_cases/:test_case_id/test_case_executions`
- **Auth:** Required
- **Response:** `201 Created`

#### Get Execution
- **Endpoint:** `GET /test_case_executions/:test_case_execution_id`
- **Auth:** Required
- **Response:** `200 OK`

#### Cancel Execution
- **Endpoint:** `PUT /test_case_executions/:test_case_execution_id/cancel`
- **Auth:** Required
- **Response:** `200 OK`

---

### Test Case Steps

#### Get Step
- **Endpoint:** `GET /test_case_steps/:test_case_step_id`
- **Auth:** Required
- **Response:** `200 OK`

#### Clean Step
- **Endpoint:** `PUT /test_case_steps/:test_case_step_id/clean`
- **Auth:** Required
- **Response:** `200 OK`

---

### Test Case Step Executions

#### Create Execution
- **Endpoint:** `POST /test_case_step_executions`
- **Auth:** Required
- **Request Body:** Step execution details
- **Response:** `201 Created`

#### Update Execution
- **Endpoint:** `PUT /test_case_step_executions/:test_case_step_execution_id`
- **Auth:** Required
- **Response:** `200 OK`

---

### Test Cycles

#### Get Test Cycle
- **Endpoint:** `GET /test_cycles/:test_cycle_id`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Counters
- **Endpoint:** `GET /test_cycles/:test_cycle_id/counters`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Team
- **Endpoint:** `GET /test_cycles/:test_cycle_id/team`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Device Configurations
- **Endpoint:** `GET /test_cycles/:test_cycle_id/device_configurations`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Permissions
- **Endpoint:** `GET /test_cycles/:test_cycle_id/permissions`
- **Auth:** Required
- **Response:** `200 OK`

#### Get My Reproductions
- **Endpoint:** `GET /test_cycles/:test_cycle_id/my_bug_reproductions`
- **Auth:** Required
- **Response:** `200 OK`

---

### Test Features

#### Get Feature
- **Endpoint:** `GET /test_features/:test_feature_id`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Read Features
- **Endpoint:** `GET /test_features/read`
- **Auth:** Required
- **Response:** `200 OK`

---

### Test Sessions

#### Get Sessions
- **Endpoint:** `GET /test_sessions`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Session Details
- **Endpoint:** `GET /test_sessions/:test_session_id`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Active Session
- **Endpoint:** `GET /test_sessions/active`
- **Auth:** Required
- **Response:** `200 OK`

#### Create Session
- **Endpoint:** `POST /test_cycles/:test_cycle_id/test_sessions`
- **Auth:** Required
- **Response:** `201 Created`

#### Extend Session
- **Endpoint:** `PUT /test_sessions/:test_session_id/extend`
- **Auth:** Required
- **Response:** `200 OK`

#### Finish Session
- **Endpoint:** `PUT /test_sessions/:test_session_id/finish`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Extension Options
- **Endpoint:** `GET /test_sessions/:test_session_id/extensions`
- **Auth:** Required
- **Response:** `200 OK`

---

### Tester Invitations

#### Get Pending Invitations
- **Endpoint:** `GET /tester_invitations/pending`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Accepted Invitations
- **Endpoint:** `GET /tester_invitations/accepted`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Locked Invitations
- **Endpoint:** `GET /tester_invitations/locked`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Single Invitation
- **Endpoint:** `GET /tester_invitations/:tester_invitation_id`
- **Auth:** Required
- **Response:** `200 OK`

#### Accept Invitation
- **Endpoint:** `PUT /tester_invitations/:tester_invitation_id/accept`
- **Auth:** Required
- **Response:** `200 OK`

#### Reject Invitation
- **Endpoint:** `PUT /tester_invitations/:tester_invitation_id/reject`
- **Auth:** Required
- **Request Body:** Rejection reason
- **Response:** `200 OK`

#### Get Reject Reasons
- **Endpoint:** `GET /tester_invitations/reject_reasons`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Quit Reasons
- **Endpoint:** `GET /tester_invitations/quit_reasons`
- **Auth:** Required
- **Response:** `200 OK`

#### Quit Test Cycle
- **Endpoint:** `PUT /tester_invitations/:tester_invitation_id/quit`
- **Auth:** Required
- **Request Body:** Quit reason
- **Response:** `200 OK`

#### Get Invitation Permissions
- **Endpoint:** `GET /tester_invitations/:tester_invitation_id/permissions`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Invitations
- **Endpoint:** `GET /tester_invitations`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Invitation Counts
- **Endpoint:** `GET /tester_invitations/counts`
- **Auth:** Required
- **Response:** `200 OK`

#### Create Access
- **Endpoint:** `POST /tester_invitations/:tester_invitation_id/access`
- **Auth:** Required
- **Response:** `201 Created`

#### Get Test Cycle Counters
- **Endpoint:** `GET /tester_invitations/:tester_invitation_id/test_cycle_counters`
- **Auth:** Required
- **Response:** `200 OK`

---

### Testers

#### Get Tester Details
- **Endpoint:** `GET /testers/:tester_id`
- **Auth:** Required
- **Response:** `200 OK`

#### Delete Tester
- **Endpoint:** `DELETE /testers/:tester_id`
- **Auth:** Required
- **Response:** `200 OK`

#### Create Tester (Deprecated)
- **Endpoint:** `POST /testers`
- **Auth:** Required
- **Note:** "Use new sign-up flow through Cirro"
- **Response:** `201 Created`

---

### User Story Versions

#### Get Version
- **Endpoint:** `GET /user_story_versions/:user_story_version_id`
- **Auth:** Required
- **Response:** `200 OK`

---

### User Story Version Executions

#### Create Execution
- **Endpoint:** `POST /user_story_versions/:user_story_version_id/user_story_version_executions`
- **Auth:** Required
- **Response:** `201 Created`

#### Get Execution
- **Endpoint:** `GET /user_story_version_executions/:user_story_version_execution_id`
- **Auth:** Required
- **Response:** `200 OK`

#### Submit Execution
- **Endpoint:** `PUT /user_story_version_executions/:user_story_version_execution_id/submit`
- **Auth:** Required
- **Response:** `200 OK`

#### Cancel Execution
- **Endpoint:** `PUT /user_story_version_executions/:user_story_version_execution_id/cancel`
- **Auth:** Required
- **Response:** `200 OK`

---

### Activity Dashboard

#### Get Time Filters
- **Endpoint:** `GET /tester_activity_dashboard/time_filters`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Activity Summary
- **Endpoint:** `GET /tester_activity_dashboard/summary`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Bugs List
- **Endpoint:** `GET /tester_activity_dashboard/bugs`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Tests List
- **Endpoint:** `GET /tester_activity_dashboard/tests`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Session Reports
- **Endpoint:** `GET /tester_activity_dashboard/session_reports`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Bug Reproductions
- **Endpoint:** `GET /tester_activity_dashboard/bug_reproductions`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Bug Disputes
- **Endpoint:** `GET /tester_activity_dashboard/bug_disputes`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Bug Fix Confirmations
- **Endpoint:** `GET /tester_activity_dashboard/bug_fix_confirmations`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Bug Report Confirmations
- **Endpoint:** `GET /tester_activity_dashboard/bug_report_confirmations`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Test Cases
- **Endpoint:** `GET /tester_activity_dashboard/test_cases`
- **Auth:** Required
- **Response:** `200 OK`

#### Get User Stories
- **Endpoint:** `GET /tester_activity_dashboard/user_stories`
- **Auth:** Required
- **Response:** `200 OK`

---

### Rankings

#### Get Current Rankings
- **Endpoint:** `GET /tester_rankings/current`
- **Auth:** Required
- **Response:** `200 OK`

---

### Other Endpoints

#### Get App Rate Info
- **Endpoint:** `GET /app_rate_requests/info`
- **Auth:** Required
- **Response:** `200 OK`
  ```json
  {
    "info": {
      "ask_to_rate": "boolean"
    }
  }
  ```

#### Create App Rate Request
- **Endpoint:** `POST /app_rate_requests`
- **Auth:** Required
- **Request Body:**
  ```json
  {
    "app_rate_request": {
      "answer_option": "string (accepted|declined)"
    }
  }
  ```
- **Response:** `201 Created`

#### Create Tester Action
- **Endpoint:** `POST /tester_actions`
- **Auth:** Required
- **Response:** `201 Created`

#### Get Tester Leave Reasons
- **Endpoint:** `GET /tester_leave_reasons`
- **Auth:** Required
- **Response:** `200 OK`

#### Get Current Activity
- **Endpoint:** `GET /current_activity`
- **Auth:** Required
- **Response:** `200 OK`

#### Read Feature Description
- **Endpoint:** `PUT /tester_read_confirmation/:feature_id`
- **Auth:** Required
- **Response:** `200 OK`

#### Create Onboarding Submission
- **Endpoint:** `POST /onboarding_submissions`
- **Auth:** Required
- **Response:** `201 Created`

---

## Common Response Patterns

### Success Responses
- `200 OK` - Standard successful GET request
- `201 Created` - Successful creation (POST)
- `200 OK` - Successful update (PUT)
- `200 OK` - Successful deletion (DELETE)

### Common Error Responses
- `400 Bad Request` - Invalid parameters
- `401 Unauthorized` - Missing/invalid auth token
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation errors

### Standard Status Object
Most responses include timestamps in ISO 8601 format (e.g., "2025-02-07T11:44:31Z")

---

## Standard Object Structures

### User Profile
```json
{
  "id": "integer",
  "screenname": "string",
  "avatar_url": "string",
  "level": "string or null",
  "name": "string"
}
```

### Status Enum
```json
{
  "key": "string (submitted|accepted|rejected|in_progress)",
  "icon_name": "string",
  "name": "string"
}
```

### Device Configuration
```json
{
  "id": "integer",
  "device": {
    "id": "integer",
    "name": "string",
    "category": { "key": "string", "name": "string" },
    "vendor": { "name": "string" },
    "operating_system": { "key": "string", "name": "string" }
  },
  "operating_system_version": { "name": "string" },
  "browsers": [
    {
      "id": "integer",
      "name": "string",
      "key": "string"
    }
  ]
}
```

---

## Authentication

All endpoints require Bearer token authentication via the `Authorization` header:
```
Authorization: [token_value]
```

Tokens can be obtained via the OAuth endpoint or created via the AccessTokens endpoint.
