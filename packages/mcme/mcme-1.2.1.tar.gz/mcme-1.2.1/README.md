# MCME - Meshcapade Me Command Line Client

Welcome to the age of Avatars, introducing the Meshcapade Me CLI (MCME). Create accurate digital doubles from any source of data in a unified 3D body format for every industry.
Built on our [patented avatar technology](https://meshcapade.com/SMPL), MCME simplifies the avatar creation process, allowing you to create and download avatars directly from your terminal. This interface is ideal for users who favor terminal-based interactions or seek seamless integration of avatar creation into automated processes. If you prefer alternative methods, we've got you covered with an [API](https://meshcapade.com/docs/api) and a [Web UI](https://me.meshcapade.com/vault) for creating, editing, and downloading avatars.

## Installation

MCME requires **Python 3.9+**

To ensure a clean and isolated installation, we recommend using a virtual environment (venv). Here's an example of how to set up MCME within a virtual environment:

```bash
# Create a virtual environment
python3.10 -m venv mcme_env

# Activate the virtual environment
source mcme_env/bin/activate  
# On Windows, use `mcme_env\Scripts\activate`

# Install MCME
pip install mcme
```

## Usage

To make sure the installation worked and to view the general help, execute the following command:

```bash
mcme --help
```

### Authentication
To authenticate with MCME, use your [mehscapade.me](https://me.meshcapade.com/vault) credentials. If you haven't registered yet, take a moment to sign up for a free account. For now, when setting up for CLI access, please register using a username and password. Single Sign-On (SSO) support is on its way and will be available soon!

When you execute mcme for the first time or after your access token has expired, you will be prompted for username and password. Alternatively you can set them using:
```bash
mcme --username <your_username> --password <your_password>
```
Or save them as environment variables:
```bash
export MCME_USERNAME=<your_username>
export MCME_PASSWORD=<your_password>
```

### Credits

> Please be aware that creating avatars consumes credits, provided the creation is successful. Creating an avatar from betas, measurements or images costs **200 credits**, creating one from scans or videos costs **500 credits**. You can check your current credit balance at any time by using the following command:

```bash
mcme user-info
```
If you find yourself running low on credits or wish to purchase more, visit our [credits page](https://me.meshcapade.com/credits).

### Avatar Creation

Generate unique avatars effortlessly with the `mcme create` command. To explore the available methods and options, use:
```bash
mcme create --help
```

Here's an example command:

> Using this command to successfully create an avatar from images incurs a charge of 200 credits.

```bash
mcme create from-images --gender FEMALE --name my_cli_avatar --input /path/to/image.jpg --height 165 --weight 60 --image-mode AFI
```

Customize the avatar creation with the following options:

- `--gender [MALE|FEMALE|NEUTRAL]`: Specify the gender of the created avatar.  
- `--name TEXT`: Assign a name to the created avatar.  
- `--input FILE`: Provide the path to the input image.  
- `--height INTEGER`: Specify the height of the person in - the image.  
- `--weight INTEGER`: Specify the weight of the person in - the image.  
- `--image-mode [AFI|BEDLAM_CLIFF]`: Choose the mode for avatar creation.

### Avatar Creation with Immediate Download

If you want to download the avatar immediately after creation, you can include download options by appending them after the `create` command:

> Using this command to successfully create an avatar from images incurs a charge of 200 credits.

```bash
mcme create --download-format obj --pose T --compatibility-mode DEFAULT --out-file /path/to/output/file.obj from-images ...
```

This command allows you to specify various download options:

- `--download-format [OBJ|FBX]`: Choose the format for - downloading the avatar, either OBJ or FBX.  
- `--pose [T|A|I|SCAN]`: Select the desired pose for the - downloaded avatar. Note that SCAN is only applicable for - avatars created from images, as it corresponds to the - pose of the person captured in the image.  
- `--compatibility-mode [DEFAULT|OPTITEX|UNREAL]`: Adjust - output for compatibility with selected software.  
- `--out-file FILE`: Specify a file to save the created avatar mesh to.

### Avatar Download

To download avatars created using MCME, the API, or the Web UI associated with your account, use the ```mcme download``` command. Customize the download with the options shown in [Avatar Creation with Immediate Download](#avatar-creation-with-immediate-download)
 or explore them using:
```bash
mcme download --help
```
Executing the download command initiates an export job, and after a brief processing time, your avatar will be downloaded to the current working directory. 

If you choose not to specify the asset ID directly, the command lists the last ten avatars you created, allowing you to choose which one to download. Use the option `--show-max-avatars` to list more than ten avatars.
