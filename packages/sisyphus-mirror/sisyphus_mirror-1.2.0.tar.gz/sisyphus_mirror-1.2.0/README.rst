##################
Sisyphus Mirror Py
##################
English | `Русский <https://github.com/rigilfanov/sisyphus-mirror-py/blob/master/README_RU.rst>`_

A modern Python implementation of the tool for mirroring the `Sisyphus <https://packages.altlinux.org>`_ repository.

The project is inspired by the original utility `sisyphus-mirror <https://git.altlinux.org/gears/s/sisyphus-mirror.git>`_.

Technical Requirements
======================
* GNU/Linux OS  
* Python 3.12+  
* RSync 3.2+  
* 110+ GB of free disk space  

Installation
============
.. code-block:: bash

  # Create dedicated user and directories:
  useradd -rMU -d /opt/sisyphus-mirror -s /usr/sbin/nologin sisyphus-mirror
  mkdir -p /etc/sisyphus-mirror /opt/sisyphus-mirror /srv/mirrors/altlinux
  chown sisyphus-mirror:sisyphus-mirror /opt/sisyphus-mirror
  chown sisyphus-mirror:sisyphus-mirror /srv/mirrors/altlinux

  # Create Python virtual environment and install the package:
  sudo -u sisyphus-mirror python3 -m venv /opt/sisyphus-mirror/venv
  sudo -u sisyphus-mirror /opt/sisyphus-mirror/venv/bin/pip install sisyphus-mirror

  # Add command
  ln -s /opt/sisyphus-mirror/venv/bin/sisyphus-mirror /usr/local/sbin/sisyphus-mirror

  # Create TOML configuration file:
  echo '[sisyphus-mirror]
  dry_run = false
  verbose = false
  debug = false

  # Explicitly defined repository branches.
  branch_list = ["p11"]

  # Repository source URL.
  source_url = "rsync://ftp.altlinux.org/ALTLinux"

  # Working directory for snapshots and temporary synchronization data.
  working_dir = "/srv/mirrors/altlinux"

  # Target CPU architectures.
  arch_list = ["noarch", "x86_64", "x86_64-i586"]

  # Additional paths for finding and creating hard links to unchanged files.
  linkdest_list = []

  # Additional file include patterns.
  include_files = ["list/**", ".timestamp"]

  # Additional file exclude patterns.
  exclude_files = ["*debuginfo*", "SRPMS"]

  # Maximum number of snapshots per branch.
  snapshot_limit = 1

  # Limiting network I/O bandwidth.
  rate_limit = "5m"

  # Connection timeout (seconds).
  conn_timeout = 60

  # I/O timeout (seconds).
  io_timeout = 600' > /etc/sisyphus-mirror/default.toml

Modify configuration if needed:

.. code-block:: bash

  nano /etc/sisyphus-mirror/default.toml

Test Run
========
Dry-run synchronization with detailed output:

.. code-block:: bash

  sudo -u sisyphus-mirror sisyphus-mirror --dry-run --verbose

Ensure that the reported `total size` fits the available disk space.

Production Run
==============
Actual synchronization:

.. code-block:: bash

  sudo -u sisyphus-mirror sisyphus-mirror

Systemd Integration
===================
.. code-block:: bash

  # systemd service unit:
  echo '[Unit]
  Description=sisyphus-mirror service
  Wants=sisyphus-mirror.timer

  [Service]
  Type=oneshot
  User=sisyphus-mirror
  Group=sisyphus-mirror
  ExecStart=sisyphus-mirror
  ProtectHome=true
  ProtectSystem=true
  SyslogIdentifier=sisyphus-mirror

  [Install]
  WantedBy=multi-user.target' > /etc/systemd/system/sisyphus-mirror.service

  # Daily timer:
  echo '[Unit]
  Description=Periodic run of sisyphus-mirror

  [Timer]
  # Run at a random time between 00:15 and 07:45 local server time
  OnCalendar=*-*-* 00:15:00
  RandomizedDelaySec=7h 30min
  Persistent=true
  Unit=sisyphus-mirror.service

  [Install]
  WantedBy=timers.target' > /etc/systemd/system/sisyphus-mirror.timer

  # Reloading systemd configuration and activating the timer:
  systemctl daemon-reload
  systemctl enable --now sisyphus-mirror.timer

Serving via rsyncd
==================
Example for a previously unconfigured rsync installation:

.. code-block:: bash

  echo 'port = 873
  uid = 65534
  gid = 65534
  # Using chroot is required
  use chroot = yes
  max connections = 30

  [altlinux]
  path = /srv/mirrors/altlinux
  read only = yes
  list = yes' > /etc/rsyncd.conf

  systemctl enable rsync
  systemctl restart rsync

Serving via Nginx
=================
Example for a previously unconfigured Nginx installation:

.. code-block:: bash

  echo 'server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    location /altlinux/ {
        alias /srv/mirrors/altlinux/;
        index off;
        autoindex on;
        autoindex_exact_size off;
        autoindex_localtime on;
        try_files $uri $uri/ =404;
    }
  }' > /etc/nginx/sites-available/altlinux

  rm /etc/nginx/sites-enabled/default
  ln -s /etc/nginx/sites-available/altlinux /etc/nginx/sites-enabled/altlinux

  systemctl enable nginx
  systemctl restart nginx
