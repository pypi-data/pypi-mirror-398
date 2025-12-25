<!--
Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com

This work is licensed under the Creative Commons Attribution-ShareAlike 4.0
International License. To view a copy of this license, visit
http://creativecommons.org/licenses/by-sa/4.0/ or send a letter to Creative
Commons, PO Box 1866, Mountain View, CA 94042, USA.
-->

# Security Notes

Exposing an application to the Internet introduces potential security risks. To minimize vulnerabilities, it is essential to implement best practices when exposing `gemseo-http`. Follow these recommendations to safeguard your application:

1. **Use a Reverse Proxy with SSL/TLS Encryption**
   Protect the data in transit by setting up `gemseo-http` behind a reverse proxy that enforces SSL/TLS encryption.

2. **Deploy Behind a Firewall**
   Restrict unauthorized access by placing the application behind a properly configured firewall.

3. **Host Segregation**
   Run the application on a segregated host to limit potential damage. This ensures that a compromise of the host does not affect your entire infrastructure.

4. **Containerization or Sandboxing**
   Operate the application in a sandboxed environment, such as a Docker container or a chroot jail, to reduce exposure.

Additionally, make it a habit to:

- Regularly visit the `gemseo-http` webpage to stay updated with the latest versions of the package and its dependencies.
- Monitor security advisories to act promptly in case of reported vulnerabilities.

By following these measures, you can significantly enhance the security of your `gemseo-http` application.
