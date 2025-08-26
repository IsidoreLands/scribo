import typer
import paramiko
import os
import logging
import importlib.resources

app = typer.Typer(name="praetor", help="The Fleet Commander for the Scriptor ecosystem.")

def get_template(filename):
    """Loads a template file from within the installed package."""
    try:
        # This is the modern, correct way to access package data
        return importlib.resources.read_text('scriptor.templates.sm_sensor', filename)
    except FileNotFoundError:
        logging.error(f"Template file '{filename}' not found in package.")
        return None

@app.command()
def deploy_sensor(
    target: str = typer.Argument(..., help="The target host in 'user@hostname' format."),
    key_filename: str = typer.Option(None, "--key", "-k", help="Path to your private SSH key.")
):
    """
    Deploys the System Maneuverability sensor to a target host.
    """
    logging.info(f"Praetor: Initiating sensor deployment to {target}...")
    
    try:
        user, host = target.split('@')
    except ValueError:
        logging.error("Praetor: Invalid target format. Must be 'user@hostname'.")
        raise typer.Exit(code=1)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        logging.info(f"Connecting to {host} as {user}...")
        ssh.connect(hostname=host, username=user, key_filename=key_filename)
        sftp = ssh.open_sftp()
        logging.info("Connection successful.")

        remote_dir = f"/home/{user}/system_maneuverability"
        logging.info(f"Creating remote directory: {remote_dir}")
        sftp.mkdir(remote_dir)
    except FileExistsError:
        logging.info("Remote directory already exists.")
    except Exception as e:
        logging.error(f"Praetor: Failed to connect or create directory: {e}")
        raise typer.Exit(code=1)

    try:
        # Template and upload scripts
        scripts_to_deploy = ["get_sm_score.py", "detect_gpu.sh", "log_sm_score.sh"]
        for script_name in scripts_to_deploy:
            logging.info(f"Deploying '{script_name}'...")
            content = get_template(script_name)
            if not content: continue
            
            # Replace the hardcoded home directory with the target user's home
            templated_content = content.replace("/home/isidore", f"/home/{user}")
            
            remote_path = f"{remote_dir}/{script_name}"
            with sftp.file(remote_path, 'w') as remote_file:
                remote_file.write(templated_content)
            
            # Make the script executable
            sftp.chmod(remote_path, 0o755)

        # Set up the cron job
        logging.info("Setting up cron job for log_sm_score.sh...")
        cron_command = f"* * * * * {remote_dir}/log_sm_score.sh"
        # This is the standard, idempotent way to add a cron job
        stdin, stdout, stderr = ssh.exec_command(f'(crontab -l 2>/dev/null; echo "{cron_command}") | crontab -')
        
        if stdout.channel.recv_exit_status() != 0:
            logging.error(f"Failed to set up cron job. STDERR: {stderr.read().decode()}")
        else:
            logging.info("Cron job successfully installed.")

        logging.info("Praetor: Sensor deployment complete. Mutatis mutandis.")

    finally:
        sftp.close()
        ssh.close()
        logging.info("Connection closed.")
