# Git-based CTF

Git-based CTF is a novel attack-and-defense CTF platform that can be easily
hosted as an in-course activity proposed in our [paper](https://www.usenix.org/system/files/conference/ase18/ase18-paper_wi.pdf) at USENIX ASE. This
repository contains [scripts](scripts) for automating `Git-based CTF`. To
see how to configure and play Git-based CTF, see the followings.

**If you want to see the version covered in our
[paper](https://www.usenix.org/system/files/conference/ase18/ase18-paper_wi.pdf)
at USENIX ASE, please refer to [ase](../../tree/ase) branch.**

In this repo, [AlexOConnorHub](https://www.github.com/AlexOConnorHub) has modified and updated this projet. This repo uses a [`Dockerfile`](./Dockerfile) to provide a webpage to manage this. It also is planning on using a Github Organization to host the CTF, which will make the cleanup afterwards easier, allowing those involved not wondering if they should keep a bunch of "team-x" repos around.

## Setup

### Steps

1. Instructors should setup the `config.json` file. First, a [personal access token](https://github.com/settings/tokens) will need to be generated. Then, taking the generated token, run the two following commands:

   - `docker build . -t "gitctf" --build-arg GH_TOKEN_BUILD="<INSERT_YOUR_PERSONAL_TOKEN_HERE>"`
   - `docker run -dit --rm -p 9000:80 --name git gitctf`

    This will start the admin portal for Git-based CTF on port 9000. Follow the instructions for setting up the `config.json` file. After that, the `config.json` will be available at the Github Organization's webpage (`organization-name.github.io`).

2. Students need to obtain the `config.json` file
   prepared by the instructors in Step 1.

3. Each team should prepare for a PGP public & private key pair in their own
   machine. The teams' public keys should be distributed through a pull request from one of the teammates.

4. Each student should install GPG and Docker on their own machine in
   order to play CTF.

## For Students

Git-based CTF consists of three major steps: preparation, injection, and
exercise. We provide a set of tools that help students play the CTF for each
step.

## 1. Preparation Step

In this step, you need to prepare a network service running in a Docker
container. The final outcome of this step is a Git repository that contains a
Dockerfile as well as source code for the service program. We provide several
useful tools and scripts that help create such a service container.

- We provide a template [Dockerfile](templates/service_template/Dockerfile), which can be used to
  prepare a service application.

- You can check whether a service repository is valid or not by running:

    ```bash
    ./gitctf.py verify service --team [TEAMNAME] --branch [BRANCH]
    ```
  
  The above command checks whether the BRANCH branch of the repository follows
  the Git-based CTF convention.

## 2. Injection Step

You should inject vulnerabilities into the service application prepared in the
previous step. You should also provide a working exploit for each injected
vulnerability as a proof. An exploit in Git-based CTF is a program running in a
Docker container, and it should follow a specific format, e.g., it should be
properly encrypted and signed. We provide several tools and scripts that help
creating and verifying injected vulnerabilities and exploits.

- You should write an exploit program/script using the template
  [Dockerfile](templates/exploit_template/Dockerfile) we provided.

- You can verify your exploit against a service of a specific version (i.e.,
  specific branch). Assume that you have a local copy of a target service at
  SRVDIR, and your exploit at EXPDIR. You can then run the following command to
  test whether your exploit works within a SEC seconds against the BRANCH branch version of the
  service:

    ```bash
    ./gitctf.py verify exploit --exploit [EXPDIR] --service-dir [SRVDIR] --branch [BRANCH] --timeout [SEC]
    ```

  Also, if you add the ```--encrypt``` option, you can encrypt the exploit when
  it gets verified. You should upload (i.e. commit and push) this encrypted
  exploit, which will be named as ```exploit_bugN.zip.pgp``` in the root
  directory of each branch. Here, ```bugN``` is the corresponding branch name.

- After uploading all the exploits, you can verify your submitted exploits
  against each branch of your service, with the following command.

    ```bash
    ./gitctf.py verify injection --team [TEAMNAME]
    ```

## 3. Exercise Step

In this step, you finally play the actual CTF game. To attack other opponents,
you should create an issue that contains an encrypted attack described in the
previous step.

- To prepare for an attack, you should create a zip file that has a directory
  containing an exploit Dockerfile as well as an exploit script/program. You
  then sign and encrypt the zipped directory, and submit it as an issue in the
  target team's repository. Assuming that you have a local copy of a target
  service at SRVDIR, and your exploit at EXPDIR, the following command will
  perform these steps automatically.

    ```bash
    ./gitctf.py submit --exploit [EXPDIR] --service-dir [SRVDIR] --target [TEAMNAME]
    ```

- You can see issues in your own repository to check whether you are attacked by
  other opponents. Since each issue is encrypted with your own key, you can
  download the attack and replay it in your own local machine. Especially, you
  may want to analyze how an unintended vulnerability is exploited. To verify
  unintended exploit, you can use `gitctf.py verify exploit` command described
  above.

- You can also check your score with our tool. Assuming that the scoreboard
  repository URL is properly given by `config.json` file, you can invoke the
  following command to see the current score.

    ```bash
    ./gitctf.py score
    ```

  Note that the points you see from the above command may slightly differ from
  the actual points computed at the instructor's machine, because this command
  relies on the system time to compute the unintended points.
  Also, This command automatically populates an HTML file `score.html` that
  shows a graph representing score over time for each team or person.

## For Instructors

There should be a machine that is dedicated to evaluating the attacks in
Git-based CTF. The machine needs to be time-synchronized with an NTP server.

- Create the repository of scoreboard. You can check out an example
  [scoreboard](https://github.com/KAIST-IS521/2018s-gitctf-score).

- Click the `Watch` button in each team's service repository.

- After the injection phase, you need to create a
  [`config.json`](configuration/config.json) file, which describes the
  [basic settings](#configuration) for a CTF.

- After the injection phase, you need to fill the commit hash of N-th injected
  bug of each team, with the following command.

    ```bash
    ./gitctf.py hash
    ```

- During the exercise phase, the machine should run the following command
  assuming that you have a proper set-up for the ssh-agent and the gpg-agent,
  because this command will invoke a series of `ssh` and `gpg` commands, and
  such commands require a user to enter a passphrase.

    ```bash
    ./gitctf.py eval --token API_TOKEN
    ```

  This command will run in an infinite loop, automatically fetch issues from
  the repositories, and update the scoreboard. This process will be killed when
  CTF is finished.

## Configuration

[This file](configuration/config.json) contains critical information for managing
Git-based CTF. This script must be created by an instructor, and distributed to
students before a CTF begins. You can check out an [example configuration file](https://github.com/KAIST-IS521/2018-Spring/blob/master/Activities/config.json)

### [config.json](configuration/config.json) keys

1. `repo_owner`: The name of the owner of the CTF repositories.
1. `intended_pts`: Points for exploiting an intended vulnerability.
1. `unintended_pts`: Points for exploiting an unintended vulnerability.
1. `round_frequency`: How often will our system change the round? (in sec.)
1. `start_time`: When does the exercise phase start? You should put a string in the ISO8601
   format, e.g., you can use `date -Iseconds`.
1. `end_time`: When does this CTF finish? You should put a string in the ISO8601
   format.
1. `exploit_timeout`: Timeout for exploit. (in sec.)
    1. `exercise_phase`: Timeout when verify exploit in exercise phase.
    1. `injection_phase`: Timeout when verify exploit in injection phase.
1. `template_path`: This is the path within the Docker container where the
   templates are stored.
1. `instructor`: The Github username of the instructor.
1. `problems`: The information reguarding each problem.
   1. `problem-N`: Problem description for problem-N.
      1. `base_image`: Docker image for the problem.
      1. `sed_cmd`: sed command for setting up the repositories for the image.
      1. `service_exe_type`: Service type.
      1. `number_of_bugs`: Number of bugs injected.
      1. `injection_points`: Points for injecting the problem.
      1. `description`: Description of the problem.
      1. `bin_src_path`: Bin source path.
      1. `bin_dst_path`: Bin destination path.
      1. `flag_dst_path`: Flag destination path.
      1. `bin_args`: Bin arguments.
      1. `port`: Port of the service.
      1. `required_packages`: Packages required for the service.
      1. `injection_target_commit_hash_enc_sign`: Target commit hash of the injection, encrypted and signed.
1. `teams`: Participating teams' information.
    1. `pub_key_id`: The public key ID of the team.
    2. `problem-N` The problem for which the data is relevant
       1. `repo_name`: The URL for each team's service repository.
       2. `bug-N`: The commit hash of the N-th injected bug of this team.
1. `individual`: Participating individuals' information. Each field is separated
   by participants' GitHub IDs.
    1. `pub_key_id`: The public key ID of the individual.
    2. `team`: Which team does this individual belong to?

## Authors

This research project has been conducted by [SoftSec Lab](https://softsec.kaist.ac.kr) at KAIST.

- Seongil Wi
- [Jaeseung Choi](https://softsec.kaist.ac.kr/~jschoi/)
- [Sang Kil Cha](https://softsec.kaist.ac.kr/~sangkilc/)

Updating this to Python3, adapting to using GitHub Organizations, and adding managment of page for the admin.

- [Alex O'Connor](https://www.github.com/AlexOConnorHub)

## Citing Git-based CTF

To cite our paper:

```bibtex
@INPROCEEDINGS{wi:usenixase:2018,
    author = {SeongIl Wi and Jaeseung Choi and Sang Kil Cha},
    title = {Git-based {CTF}: A Simple and Effective Approach to Organizing In-Course Attack-and-Defense Security Competition},
    booktitle = {2018 {USENIX} Workshop on Advances in Security Education ({ASE} 18)},
    year = {2018}
}
```

## License

This project is licensed under the [Apache License](LICENSE.md)

## Acknowledgement

We thank GitHub for providing unlimited free plan for organizing classes. We also thank HyungSeok Han and anonymous reviewers for their constructive feedback. This work was supported by Institute for Information & communications Technology Promotion (IITP) grant funded by the Korea government (MSIT)
