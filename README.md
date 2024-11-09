[English](README.md) | [Chinese](README.zh.md)

## Functionality

Expandable 301-like one-click web page deployment

Note: It is better to install this program in a brand new machine, this program will automatically deploy the environment and guide the user to input the desired domain name and the target domain name, similar to the implementation of the user to input `aaa.com` and jump to the user's desired `bbb.com`, the domain of `aaa.com` must be the user's own.

## How to use

1. First clone the repository
   `git clone https://github.com/Catchabox/redirecting-page.git`

2. Give the program execution privileges
   `chmod +x *`

3. First run `env` to automatically deploy your environment.
   /env`. /env`.
   The program will automatically install nginx and PHP-FPM.

4. Resolve the domain name `aaa.com` to your machine.
   `A X.X.X.X`.

5. Execute the deployment jump program again
   `. /install`.

   The program will automatically apply for the certificate and deploy the web page automatically.

   Note: If the local PHP environment already exists, it may be overwritten, so it is recommended to use a machine without PHP and nginx installed to install and deploy, of course, the subsequent will come out of the Docker version to circumvent this problem, if you want to cancel the jump just now, you can execute `. /uninstall` to uninstall the page you just deployed, and remove the certificate you just applied for.

6. If you want to change the page you just jumped to, for example, `aaa.com -> bbb.com` and now you want to change it to `aaa.com -> ccc.com`, then you can change it via `aaa.com/edit.html`, the password is written in the `upadte.php` file, and the default is `XXXXXXX`. It is highly recommended to change
