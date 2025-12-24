# ezoff

Python package for interacting with the EZOffice API. Largely uses v2 API endpoints, a couple v1 are used in cases where there aren't any documented v2 versions. Additionally, a few of the JSON API endpoints (found using the browser console) are supported.

- [v1 API Documentation](https://ezo.io/ezofficeinventory/developers/)
- [v2 API Documentation](https://ezo.io/ezofficeinventory/api-v2/)

## Installation

`pip install ezoff`

## Usage

Two environment variables are required for ezoff to function.

| Env Variable | Description |
| --------- | ----------- |
| EZO_SUBDOMAIN | Should be your company name. Can be found in the URL of your EZO instance, https://{companyname}.ezofficeinventory.com/ |
| EZO_TOKEN | The access token used to authenticate requests |

`python-dotenv` package is useful for loading variables from an `.env` file. Otherwise, can be done directly with `os`.

## Project Structure

Project is split up into several files depending on what area of the EZOffice API is being dealt with. largely corresponds to how the API v2 documentation is laid out, purely for organizational purposes.

## Notes

When wanting to clear a field out of its current value with an update function, generally the empty string ("") should be used as the new value.
