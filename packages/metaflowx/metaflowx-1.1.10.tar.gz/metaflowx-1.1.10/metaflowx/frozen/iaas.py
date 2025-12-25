def iaas():
    """
    Returns a detailed summary of all important IaaS points
    extracted from the user's cloud computing notes.
    """

    summary = """
Infrastructure-as-a-Service (IaaS) — Key Points

1. Definition:
   IaaS provides the fundamental building blocks of cloud infrastructure:
   virtualized hardware resources such as virtual servers, CPU, RAM, storage,
   and networking — all accessible over the internet.

2. Responsibility Split:
   - Cloud Provider manages: physical servers, storage, networking, virtualization.
   - Cloud Consumer manages: OS, middleware, runtime, applications, and data.
   This gives consumers full administrative control over the infrastructure layer.

3. Characteristics:
   - Provides raw compute resources as virtual instances.
   - Instances are configurable (CPU cores, RAM size, storage).
   - Highly scalable and flexible.
   - Pay-per-use model.
   - Not pre-configured; administrative responsibility lies on consumer.

4. Purpose:
   Used when the consumer needs deep control over infrastructure.
   Suitable for building custom environments from scratch.

5. Virtualization:
   IaaS relies heavily on virtualization.
   Virtual servers are leased based on required hardware configurations.

6. Typical use cases:
   - Hosting applications or websites.
   - Running batch jobs, simulations, or analytics using large compute power.
   - Creating virtual networks or storage systems.
   - Temporary high-resource needs (e.g., training ML models).

7. Example from notes:
   A person with 4GB RAM laptop renting 32GB RAM from cloud for a data science project.

8. Role in Cloud Hierarchy:
   IaaS forms the lowest layer of the cloud service hierarchy.
   Above it sits PaaS, then SaaS.

9. Providers:
   Amazon AWS EC2, Google Compute Engine, Microsoft Azure Virtual Machines.
    """

    return summary
