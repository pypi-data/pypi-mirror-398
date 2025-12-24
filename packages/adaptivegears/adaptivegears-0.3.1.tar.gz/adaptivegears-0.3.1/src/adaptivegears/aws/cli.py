import typer

from adaptivegears.aws.compute import EC2Instance

app = typer.Typer(help="AWS tools")
ec2_app = typer.Typer(help="EC2 instance tools")
app.add_typer(ec2_app, name="ec2")


@ec2_app.command("get")
def ec2_get(
    instance_type: str = typer.Argument(..., help="Instance type (e.g., r6g.large)"),
    region: str = typer.Option("us-east-1", "-r", "--region", help="AWS region"),
    json: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Get EC2 instance specifications."""
    instance = EC2Instance.get(instance_type, region=region)

    if json:
        print(instance.model_dump_json(indent=2))
    else:
        r = instance.resources
        print(f"Instance: {instance.instance_type} ({instance.region})")
        print(f"  Family:     {instance.instance_family}")
        print(f"  Arch:       {instance.architecture}")
        print(f"  CPU:        {r.cpu.value:.0f} {r.cpu.scale}")
        print(f"  Memory:     {r.memory.to(r.memory.scale):.0f} {r.memory.scale}")
        print(f"  Network:    {r.network.baseline.value:.2f}-{r.network.max.value:.2f} {r.network.baseline.scale}")
        print(f"  EBS IOPS:   {r.storage_iops.baseline.value}-{r.storage_iops.max.value}")
        print(f"  EBS Tput:   {r.storage_throughput.baseline.value:.2f}-{r.storage_throughput.max.value:.2f} {r.storage_throughput.baseline.scale}")
