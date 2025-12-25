def diff_paas_iaas_saas():
    """
    Returns point-by-point differences between IaaS, PaaS, and SaaS
    in a clean, exam-ready format.
    """

    summary = """
Difference Between IaaS, PaaS and SaaS (Point Format)

1. IaaS (Infrastructure as a Service):
   - Provides basic computing resources: virtual machines, CPU, RAM, storage, networking.
   - Nothing is pre-configured; consumer installs OS, middleware, runtime, applications.
   - Offers maximum control and flexibility.
   - Suitable for building custom environments from scratch.
   - Cloud provider manages hardware + virtualization only.
   - Examples: AWS EC2, Google Compute Engine, Azure VM.

2. PaaS (Platform as a Service):
   - Provides a fully managed development and deployment environment.
   - Includes OS, runtime, frameworks, development tools, compilers, web servers.
   - Consumer focuses only on writing code and deploying applications.
   - Removes infrastructure complexity.
   - Useful for rapid development and team collaboration.
   - Examples: Google App Engine, Azure App Service, AWS Elastic Beanstalk.

3. SaaS (Software as a Service):
   - Provides completely ready-to-use software applications.
   - Accessible through web browsers or mobile apps.
   - Cloud provider handles everything: infrastructure, platform, updates, security.
   - Consumer only uses the software; zero installation or maintenance required.
   - Best for productivity tools, CRM, communication and creative software.
   - Examples: Gmail, Google Docs, Office 365, Adobe Creative Cloud.

One-Line Summary:
IaaS = hardware, PaaS = development platform, SaaS = ready-made software.
    """

    return summary
