<!-- Begin NI SECURITY.md V1.0 -->

# Security

NI views the security of our software products as an important part of our
commitment to our users.  This includes source code repositories managed through the [NI](https://github.com/ni) GitHub organization.

## Reporting Security Issues

We encourage you to report security vulnerabilities to us privately so we can
follow the principle of [Coordinated Vulnerability Disclosure
(CVD)](https://vuls.cert.org/confluence/display/CVD).  This allows us time to
thoroughly investigate security issues and publicly disclose them when appropriate.

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them by sending an email to
[security@ni.com](mailto:security@ni.com) with sufficient details about the type of issue, the impact of the issue, and how to reproduce the issue.  You may use
the [NI PGP key](https://www.ni.com/en/support/security/pgp.html) to encrypt any sensitive communications you send to us. When you notify us of a potential security
issue, our remediation process includes acknowledging receipt and coordinating any
necessary response activities with you.

## Learn More

To learn more about NI Security, please see
[https://ni.com/security](https://ni.com/security)

<!-- End NI SECURITY.md -->

## The bootstrap deploy key is public on purpose

`lvaddons/systemcore-deploy/1/vi.lib/systemcore-deploy/team-key/id_ed25519` is an SSH private
key, and publishing it is intentional. Like Vagrant's insecure key, it is a well-known default
that lets a team deploy to a new robot without any setup. It is not a secret and gives no
protection: anyone with network access to a robot that still trusts it can deploy to that robot.

A team secures its robots by installing a key generated for the team and removing the bootstrap
key from them. Please don't report this key as a leaked credential.
