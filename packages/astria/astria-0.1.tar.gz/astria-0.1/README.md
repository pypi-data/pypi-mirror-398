 #  Astria 

**Astria**  is an email cleanup CLI tool that allows for fast deletion and newsletter unsubscribing.

## Prerequisites

Before using Astria, you'll need to create an app-specific password from your email provider. App passwords are special passwords that allow third-party applications to access your email account securely without using your main account password.

#### Supported email providers

- Gmail
- Outlook
- Hotmail
- iCloud


#### How to Create an App Password
**Gmail**

🔗 [Detailed Gmail App Password Guide](https://support.google.com/accounts/answer/185833)

**Outlook/Hotmail**

🔗 [Detailed Outlook App Password Guide](https://support.microsoft.com/en-us/account-billing/create-app-passwords-for-your-work-or-school-account-d8bc744a-ce3f-4d4d-89c9-eb38ab9d4137)

**iCloud**

🔗 [Detailed Icloud App Password Guide](https://support.apple.com/en-us/102654)

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install astria.

```bash
pip install astria
```
## Usage

Must run setup before any other command
``` bash
astria setup
```
Delete emails  with the ability to choose between three options:

- Delete all Newsletters
- Delete emails from a custom address
- Delete **all** emails

⚠️ Warning: emails will be deleted permanently 

``` bash
astria clean-email
```

Searches through inbox for all newsletter unsubscribe links, then saves them to "links.txt" for easy access:

```bash
astria  unsubscribe 
```

## License

[MIT](https://choosealicense.com/licenses/mit/)