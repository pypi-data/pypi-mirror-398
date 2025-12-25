import boto3
import sys
import argparse
from typing import Dict, Tuple, Optional
from botocore.exceptions import ClientError
import subprocess
import requests
import os


class AWSEC2:
    """
    A class to manage AWS EC2 instances and related operations using boto3.
    
    Provides methods to:
    - Initialize AWS sessions using profile or explicit credentials.
    - Retrieve instance metadata via IMDSv2.
    - List, start, stop, and terminate EC2 instances by their Name tag.
    - Manage AWS SSM sessions including opening port forwarding tunnels and terminating active sessions.
    - Perform AWS SSO login.
    - Clone EC2 instances by creating AMIs and launching new instances.
    - Execute SSH commands on EC2 instances using a PEM key file.
    
    Handles common AWS EC2 and SSM tasks with error handling and user-friendly output.
    """
    def __init__(
        self,
        profile_name: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        region: Optional[str] = None
    ):
        """
        Initialize the AWSEC2 instance with AWS credentials or a profile name.
        
        Parameters:
            profile_name (Optional[str]): The name of the AWS profile to use for the session.
            access_key (Optional[str]): The AWS access key ID.
            secret_key (Optional[str]): The AWS secret access key.
            region (Optional[str]): The AWS region name.
        
        Raises:
            ValueError: If neither profile_name nor both access_key and secret_key are provided.
        
        Sets up:
            - boto3 session using the provided credentials or profile.
            - EC2 resource and client.
            - SSM client.
            - Stores the profile name or marks as "custom_credentials" if using access keys.
        """
        if profile_name:
            self.session = boto3.Session(profile_name=profile_name, region_name=region)
        elif access_key and secret_key:
            self.session = boto3.Session(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
        else:
            raise ValueError("Either profile_name or access_key/secret_key must be provided.")

        self.ec2_resource = self.session.resource('ec2')
        self.ec2_client = self.session.client('ec2')
        self.ssm_client = self.session.client('ssm')
        self.profile_name = profile_name if profile_name else "custom_credentials"

    # Get IMDSv2 session token
    @staticmethod
    def get_imds_token():
        """
        Retrieve an AWS EC2 Instance Metadata Service (IMDS) v2 token.
        
        Sends a PUT request to the IMDS token endpoint to obtain a session token with a TTL of 6 hours (21600 seconds).
        This token is required for subsequent IMDS requests to enhance security.
        
        Returns:
            str: The IMDSv2 token as a string.
        
        Raises:
            requests.exceptions.RequestException: If the HTTP request to retrieve the token fails.
        """
        token_url = "http://169.254.169.254/latest/api/token"
        headers = {"X-aws-ec2-metadata-token-ttl-seconds": "21600"}
        r = requests.put(token_url, headers=headers, timeout=2)
        return r.text

    # Fetch instance-id and region using IMDSv2
    @staticmethod
    def get_instance_metadata(token, path):
        """
        Retrieve metadata from the AWS EC2 instance metadata service using a provided token.
        
        Args:
            token (str): The AWS EC2 metadata token used for authentication.
            path (str): The metadata path to query, such as 'meta-data/instance-id'.
        
        Returns:
            str: The metadata response as a string.
        
        Raises:
            requests.exceptions.RequestException: If the HTTP request fails or times out.
        """
        url = f"http://169.254.169.254/latest/{path}"
        headers = {'X-aws-ec2-metadata-token': token}
        r = requests.get(url, headers=headers, timeout=2)
        return r.text

    def get_instances(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Retrieve dictionaries of running and stopped EC2 instances.
        
        Returns:
            Tuple[Dict[str, str], Dict[str, str]]: A tuple containing two dictionaries:
                - The first dictionary maps the names of running instances to their instance IDs.
                - The second dictionary maps the names of stopped (or other state) instances to their instance IDs.
        
        If an error occurs while fetching instances, the function prints the error message and exits the program.
        """
        instances = {}
        instances_off = {}
        try:
            for instance in self.ec2_resource.instances.all():
                name = next((tag['Value'] for tag in instance.tags or [] if tag['Key'] == 'Name'), '')
                if instance.state['Name'] == 'running':
                    instances[name] = instance.id
                else:
                    instances_off[name] = instance.id
        except ClientError as e:
            print(f"Error fetching instances: {e}")
            sys.exit(1)
        return instances, instances_off

    def list_instances(self):
        """
        Prints a list of all running and stopped instances.
        
        Retrieves instances by calling the `get_instances` method, which returns two dictionaries:
        one for running instances and one for stopped instances. Each dictionary maps instance names
        to their corresponding instance IDs.
        
        The method then prints the instance IDs and names under separate headings for running and stopped instances.
        """
        running, stopped = self.get_instances()
        print("Running instances:")
        for name, instance_id in running.items():
            print(f"\tId: {instance_id}, Name: {name}")
        print("Stopped instances:")
        for name, instance_id in stopped.items():
            print(f"\tId: {instance_id}, Name: {name}")

    def kill_tunnels(self):
        """
        Terminate all active AWS Systems Manager (SSM) sessions.
        
        This method retrieves all currently active SSM sessions and terminates each one.
        If no active sessions are found, it notifies the user accordingly.
        Handles and reports any errors encountered during the termination process.
        """
        try:
            active_sessions = self.ssm_client.describe_sessions(State='Active')
            sessions = active_sessions.get('Sessions', [])
            if sessions:
                print(f"There are {len(sessions)} active sessions, killing now...", end='')
                for session in sessions:
                    session_id = session['SessionId']
                    self.ssm_client.terminate_session(SessionId=session_id)
                print("DONE!")
            else:
                print("No active sessions found.")
        except ClientError as e:
            print(f"Error killing tunnels: {e}")

    def start_instance(self, name: str):
        """
        Start a stopped EC2 instance by its name.
        
        Checks if the instance with the given name is in the stopped state, and if so, attempts to start it using the EC2 client. Prints status messages and any errors encountered during the process.
        
        Parameters:
            name (str): The name identifier of the EC2 instance to start.
        
        Returns:
            None
        """
        _, stopped = self.get_instances()
        if name not in stopped:
            print(f"Instance {name} not found or already running.")
            return
        try:
            print(f"Starting instance {name}...")
            response = self.ec2_client.start_instances(InstanceIds=[stopped[name]])
            print(response)
        except ClientError as e:
            print(f"Error starting instance: {e}")

    def stop_instance(self, name: str):
        """
        Stops a running EC2 instance identified by its name.
        
        Checks if the instance with the specified name is currently running. If found, attempts to stop the instance using the EC2 client. Prints status messages indicating the progress and any errors encountered during the stop operation.
        
        Parameters:
            name (str): The name identifier of the EC2 instance to stop.
        
        Returns:
            None
        """
        running, _ = self.get_instances()
        if name not in running:
            print(f"Instance {name} not found or already stopped.")
            return
        try:
            print(f"Stopping instance {name}...")
            response = self.ec2_client.stop_instances(InstanceIds=[running[name]])
            print(response)
        except ClientError as e:
            print(f"Error stopping instance: {e}")

    def sso_login(self):
        """
        Initiate an AWS Single Sign-On (SSO) login process using the AWS CLI for the specified profile.
        
        This method executes the `aws sso login` command as a subprocess with the profile name stored in `self.profile_name`.
        It streams and prints the command output in real-time, detects when the user is prompted to enter a code,
        and displays the code when it appears. If the profile name is missing or set to "custom_credentials",
        it notifies the user that SSO login is not supported with explicit credentials.
        
        No return value. Outputs status messages and login progress to the console.
        """
        if not self.profile_name or self.profile_name == "custom_credentials":
            print("SSO login requires a profile name. Explicit credentials don't support SSO login.")
            return

        command = f"aws sso login --profile {self.profile_name}"
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        codeline = False
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output and output.strip():
                if codeline:
                    code = output.strip()
                    print(f"This is the code: {code}")
                else:
                    print(output.strip())
                if output.strip() == 'Then enter the code:':
                    codeline = True
        if process.poll() == 0:
            print("Login successful!")

    def open_tunnel(self, target: str, local_port: int, remote_port: int):
        """
        Open an AWS SSM port forwarding tunnel from a local port to a remote port on a specified target instance.
        
        Checks if the target instance is running, then starts an AWS SSM session to forward traffic from the given local port to the specified remote port on the target instance. The method prints status messages and streams the output of the port forwarding session until it is terminated.
        
        Args:
            target (str): The identifier of the target instance to connect to.
            local_port (int): The local port number to forward from.
            remote_port (int): The remote port number on the target instance to forward to.
        """
        running, _ = self.get_instances()
        if target not in running:
            print(f"Instance {target} not found or not running.")
            return

        command = (
            f"aws ssm start-session --target {running[target]} "
            f"--document-name AWS-StartPortForwardingSession "
            f"--parameters localPortNumber={local_port},portNumber={remote_port} "
            f"--profile {self.profile_name if self.profile_name != 'custom_credentials' else ''}"
        ).strip()

        print(f"Opening tunnel to {target}\nLocal Port: {local_port}\nRemote Port: {remote_port}\n")
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output and output.strip():
                print(output.strip())
        print("Port forwarding terminated!")

    def get_instance_by_name(self, name: str):
        """
        Retrieve an EC2 instance by its Name tag.
        
        Parameters:
            name (str): The value of the Name tag to filter instances by.
        
        Returns:
            boto3.resources.factory.ec2.Instance or None: The first EC2 instance matching the given Name tag,
            or None if no such instance exists.
        """
        res = list(self.ec2_resource.instances.filter(Filters=[
            {"Name": "tag:Name", "Values": [name]}
        ]))
        return res[0] if res else None

    def delete_ami_and_snapshots(self, ami_name):
        # Find all public/private images with matching name (usually just your AMI)
        """
        Deregister all AMIs with the specified name owned by the current AWS account and delete their associated EBS snapshots.
        
        Parameters:
            ami_name (str): The name of the AMI(s) to delete.
        
        This method:
        - Retrieves all AMIs owned by the account that match the given name.
        - Deregisters each matching AMI.
        - Deletes all EBS snapshots associated with the AMI's block device mappings.
        - Handles exceptions during snapshot deletion by printing an error message.
        """
        images = self.ec2_client.describe_images(Owners=['self'],
                    Filters=[{'Name': 'name', 'Values': [ami_name]}])['Images']
        for image in images:
            image_id = image['ImageId']
            print(f"Deregistering AMI: {image_id} ({ami_name})")
            self.ec2_client.deregister_image(ImageId=image_id)
            # Delete associated snapshots
            for bd in image.get('BlockDeviceMappings', []):
                if 'Ebs' in bd and 'SnapshotId' in bd['Ebs']:
                    snap_id = bd['Ebs']['SnapshotId']
                    print(f"Deleting snapshot {snap_id}")
                    try:
                        self.ec2_client.delete_snapshot(SnapshotId=snap_id)
                    except Exception as e:
                        print(f"Could not delete snapshot {snap_id}: {e}")

    def clone_instance(self, model_name: str, clone_names: list, 
                       create_ami: bool = False, ami_id: str = None):
        """
        '''
        Clone an existing EC2 instance by creating one or more new instances based on its configuration.
        
        This method optionally creates a new Amazon Machine Image (AMI) from the source instance before launching clones.
        If `create_ami` is True, it deletes any existing AMI and snapshots with the clone AMI name, creates a new AMI,
        and waits for it to become available. Otherwise, it uses the source instance's current AMI.
        
        Parameters:
            model_name (str): The name of the existing EC2 instance to clone.
            clone_names (list): A list of names for the new cloned instances.
            create_ami (bool, optional): Whether to create a new AMI from the source instance before cloning. Defaults to False.
            ami_id (str, optional): The AMI ID to use for launching clones. If not provided, uses the source instance's AMI.
        
        Returns:
            list: A list of boto3.Instance objects representing the newly launched instances.
        
        Notes:
            - The new instances inherit the instance type, subnet, key pair, and security groups from the source instance.
            - Each new instance is tagged with its corresponding name from `clone_names`.
            - User data is configured to set an environment variable `COMPUTERNAME
        """
        import time

        model = self.get_instance_by_name(model_name)
        if not model:
            print(f"Model instance '{model_name}' not found.")
            return []        
        
        if not ami_id:
            ami_id = model.image_id
            
        if create_ami:
            ami_name = f"{model_name}-clone-ami"
            # 1. Delete old AMI & snapshots with this name, if present
            self.delete_ami_and_snapshots(ami_name)
            time.sleep(2)  # sometimes helps with eventual consistency

            print(f"Creating AMI from instance: {model_name} with name {ami_name}")
            ami = model.create_image(Name=ami_name, NoReboot=True)
            ami_id = ami.id
            print(f"AMI {ami_id} created. Waiting for it to become available...")

            waiter = self.ec2_client.get_waiter('image_available')
            waiter.wait(ImageIds=[ami_id])
            print(f"AMI {ami_id} is now available.")

        instance_type = model.instance_type
        subnet_id = model.subnet_id
        key_name = model.key_name
        sec_groups = [sg['GroupId'] for sg in model.security_groups]

        instances = []
        for name in clone_names:
            print(f"Launching new instance: {name}")
            user_data = f"""#!/bin/bash
                echo 'export COMPUTERNAME="{name}"' > /etc/profile.d/computername.sh
                chmod +x /etc/profile.d/computername.sh
                """
            res = self.ec2_resource.create_instances(
                ImageId=ami_id,   # Use the new or original AMI
                InstanceType=instance_type,
                SubnetId=subnet_id,
                SecurityGroupIds=sec_groups,
                KeyName=key_name,
                MinCount=1, MaxCount=1,
                TagSpecifications=[{
                    "ResourceType": "instance", "Tags": [{"Key": "Name", "Value": name}]
                }],
                UserData=user_data
            )
            instances.append(res[0])
            print(f"Launched: {res[0].id} as {name}")

        print("Waiting for instances to reach running state...")
        for inst in instances:
            inst.wait_until_running()
            inst.reload()
            print(f"Instance {inst.id} is running.")

        return instances

    def terminate_instances_by_name(self, names: list):
        """
        Terminate all EC2 instances that have a 'Name' tag matching any of the names provided in the list.
        
        Parameters:
            names (list): A list of instance names (strings) to identify which instances to terminate.
        
        The method filters EC2 instances by their 'Name' tag, terminates all matching instances,
        waits for each instance to be fully terminated, and prints status messages throughout the process.
        If no matching instances are found, it prints a message and returns without error.
        """
        filters = [{"Name": "tag:Name", "Values": names}]
        instances = list(self.ec2_resource.instances.filter(Filters=filters))
        if not instances:
            print("No matching instances found for termination.")
            return
        ids = [inst.id for inst in instances]
        print(f"Terminating instances: {ids}")
        self.ec2_client.terminate_instances(InstanceIds=ids)
        for inst in instances:
            inst.wait_until_terminated()
            print(f"Instance {inst.id} terminated.")

    def ssh_command(
        self,
        instance_name: str,
        pem_file: str,
        command: str,
        user: str = "ec2-user",
        extra_ssh_args: Optional[list] = None
    ) -> int:
        """
        Execute a shell command on an EC2 instance via SSH using a specified private key file.
        
        This method looks up an EC2 instance by its Name tag, verifies that it has a public DNS name,
        and then executes the given shell command on the instance over SSH. It supports specifying
        the SSH user and additional SSH command-line arguments.
        
        Args:
            instance_name (str): The Name tag of the EC2 instance to connect to.
            pem_file (str): Path to the private key (.pem) file used for SSH authentication.
            command (str): The shell command to execute on the remote instance.
            user (str, optional): The SSH username to use. Defaults to 'ec2-user'.
            extra_ssh_args (list, optional): Additional command-line arguments to pass to the ssh command.
        
        Returns:
            int: The return code from the SSH command execution. Returns 1 if the instance is not found,
                 does not have a public DNS, or if the pem_file is missing.
        """
        instance = self.get_instance_by_name(instance_name)
        if not instance:
            print(f"Instance '{instance_name}' not found.")
            return 1

        instance.load()
        public_dns = instance.public_dns_name
        if not public_dns:
            print(f"Instance '{instance_name}' does not have a public DNS (is it running and has a public IP?).")
            return 1

        if not os.path.isfile(pem_file):
            print(f"PEM file '{pem_file}' not found.")
            return 1

        ssh_args = [
            "ssh",
            "-i", pem_file,
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null"
        ]
        if extra_ssh_args:
            ssh_args.extend(extra_ssh_args)
        ssh_args.append(f"{user}@{public_dns}")
        ssh_args.append(command)

        print(f"Running SSH command on {instance_name} ({public_dns}): {command}")
        result = subprocess.run(ssh_args)
        return result.returncode


def parse_arguments():
    """
    Parse command-line arguments for the AWS EC2 Management and SSM Tunnel Tool.
    
    Supports global AWS credential options and multiple subcommands:
    - list: List all EC2 instances.
    - kill: Kill all active SSM sessions.
    - start: Start a stopped EC2 instance (requires instance name).
    - stop: Stop a running EC2 instance (requires instance name).
    - login: Perform AWS SSO login.
    - tunnel: Open an SSM port forwarding tunnel (requires target instance name, local port, and remote port).
    
    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="AWS EC2 Management and SSM Tunnel Tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Global credential arguments (must be before subcommand)
    credential_group = parser.add_argument_group("AWS Credentials")
    credential_group.add_argument("--profile", type=str, help="AWS profile name to use")
    credential_group.add_argument("--access-key", type=str, help="AWS access key ID")
    credential_group.add_argument("--secret-key", type=str, help="AWS secret access key")
    credential_group.add_argument("--region", type=str, help="AWS region (e.g., us-east-1)")

    # Subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    # List instances
    subparsers.add_parser("list", help="List all EC2 instances")

    # Kill tunnels
    subparsers.add_parser("kill", help="Kill all active SSM sessions")

    # Start instance
    parser_start = subparsers.add_parser("start", help="Start a stopped EC2 instance")
    parser_start.add_argument("instance_name", type=str, help="Name of the instance to start")

    # Stop instance
    parser_stop = subparsers.add_parser("stop", help="Stop a running EC2 instance")
    parser_stop.add_argument("instance_name", type=str, help="Name of the instance to stop")

    # SSO login
    subparsers.add_parser("login", help="Perform AWS SSO login")

    # Open tunnel
    parser_tunnel = subparsers.add_parser("tunnel", help="Open an SSM port forwarding tunnel")
    parser_tunnel.add_argument("target", type=str, help="Target instance name")
    parser_tunnel.add_argument("local_port", type=int, help="Local port number")
    parser_tunnel.add_argument("remote_port", type=int, help="Remote port number")

    return parser.parse_args()


def main():
    """
    Main function to parse command-line arguments, initialize the AWSEC2 manager with AWS credentials or profile, and execute the specified AWS EC2-related command.
    
    The function supports commands to list instances, kill tunnels, start or stop instances, perform SSO login, and open SSH tunnels. AWS credentials can be provided via a profile name or access key and secret key; if none are provided, the default profile is used.
    
    Exits the program if AWS session initialization fails.
    """
    args = parse_arguments()

    # Initialize AWSEC2 with provided credentials or default profile
    try:
        if args.profile:
            aws_manager = AWSEC2(profile_name=args.profile, region=args.region)
        elif args.access_key and args.secret_key:
            aws_manager = AWSEC2(
                access_key=args.access_key,
                secret_key=args.secret_key,
                region=args.region
            )
        else:
            aws_manager = AWSEC2(profile_name="default")
    except ValueError as e:
        print(f"Error initializing AWS session: {e}")
        sys.exit(1)

    # Execute the requested command
    if args.command == "list":
        aws_manager.list_instances()
    elif args.command == "kill":
        aws_manager.kill_tunnels()
    elif args.command == "start":
        aws_manager.start_instance(args.instance_name)
    elif args.command == "stop":
        aws_manager.stop_instance(args.instance_name)
    elif args.command == "login":
        aws_manager.sso_login()
    elif args.command == "tunnel":
        aws_manager.open_tunnel(args.target, args.local_port, args.remote_port)


if __name__ == "__main__":
    main()