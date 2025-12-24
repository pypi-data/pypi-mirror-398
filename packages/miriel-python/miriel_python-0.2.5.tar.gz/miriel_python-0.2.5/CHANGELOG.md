Changelog

All notable changes to this project will be documented in this file.

[0.2.3] - 2025-11-6
* [fix] made recognition of uris/paths more strict

[0.2.0] - 2025-10-15
* [feat] added support for append operations with learn.
* [chore] auth errors will now raise UnauthorizedError
* [feat] wait_for_complete on learn now supports exponential backoff by setting polling_interval to None
* [feat] remove_all_documents now supports removal of all documents in a single project
* [fix] delete_project now sends the proper payload

[0.1.11] - 2025-07-26
Fixing file upload so metadata can be set correctly

[0.1.10] - 2025-07-20

Changed
  • better check for urls before treating input as a bad file path 

[0.1.9] - 2025-07-18

Changed
  • first upload things that are valid filepaths, then throw error for path-like things that don't exist, then treat as strings (or always treat as string if force_string=True)

[0.1.8] - 2025-07-18

Changed
  • handling of file-like strings/paths that are invalid

Added
  • force_string parameter

[0.1.7] - 2025-07-16

Changed
	•	handling ~ for file paths

[0.1.6] - 2025-07-16

Changed
	•	File uploads now check absolute and relative paths

	•	File uploads now use learn endpoint


[0.1.5] - 2025-06-12

Added
	•	Validate presence of the API key before making any API calls. If the key is missing or empty, a ValueError is raised immediately.
	•	Error messages now include guidance directing users to https://miriel.ai to get an API key
