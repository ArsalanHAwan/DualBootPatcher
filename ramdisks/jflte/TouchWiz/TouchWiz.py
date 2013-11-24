#!/usr/bin/env python3

import common as c
import os
import re
import shutil
import sys

def modify_init_rc(directory):
  lines = c.get_lines_from_file(directory, 'init.rc')

  f = c.open_file(directory, 'init.rc', c.WRITE)
  for line in lines:
    if 'export ANDROID_ROOT' in line:
      c.write(f, line)
      c.write(f, c.whitespace(line) + "export ANDROID_CACHE /cache\n")

    elif re.search(r"mkdir /system(\s|$)", line):
      c.write(f, line)
      c.write(f, re.sub("/system", "/raw-system", line))

    elif re.search(r"mkdir /data(\s|$)", line):
      c.write(f, line)
      c.write(f, re.sub("/data", "/raw-data", line))

    elif re.search(r"mkdir /cache(\s|$)", line):
      c.write(f, line)
      c.write(f, re.sub("/cache", "/raw-cache", line))

    elif 'yaffs2' in line:
      c.write(f, re.sub(r"^", "#", line))

    elif re.search(r"^.*setprop.*selinux.reload_policy.*$", line):
      c.write(f, re.sub(r"^", "#", line))

    else:
      c.write(f, line)

  f.close()

def modify_init_qcom_rc(directory):
  lines = c.get_lines_from_file(directory, 'init.qcom.rc')

  f = c.open_file(directory, 'init.qcom.rc', c.WRITE)
  for line in lines:
    # Change /data/media to /raw-data/media
    if re.search(r"/data/media(\s|$)", line):
      c.write(f, re.sub('/data/media', '/raw-data/media', line))

    else:
      c.write(f, line)

  f.close()

def modify_fstab(directory, partition_config):
  # Ignore all contents for TouchWiz
  lines = c.get_lines_from_file(directory, 'fstab.qcom')

  system = "/dev/block/platform/msm_sdcc.1/by-name/system /raw-system ext4 ro,errors=panic wait\n"
  cache = "/dev/block/platform/msm_sdcc.1/by-name/cache /raw-cache ext4 nosuid,nodev,barrier=1 wait,check\n"
  data = "/dev/block/platform/msm_sdcc.1/by-name/userdata /raw-data ext4 nosuid,nodev,noatime,noauto_da_alloc,discard,journal_async_commit,errors=panic wait,check,encryptable=footer\n"

  system_fourth = 'ro,barrier=1,errors=panic'
  system_fifth = 'wait'
  cache_fourth = 'nosuid,nodev,barrier=1'
  cache_fifth = 'wait,check'

  # Target cache on /system partition
  target_cache_on_system = "/dev/block/platform/msm_sdcc.1/by-name/system /raw-system ext4 %s %s\n" % (cache_fourth, cache_fifth)
  # Target system on /cache partition
  target_system_on_cache = "/dev/block/platform/msm_sdcc.1/by-name/cache /raw-cache ext4 %s %s\n" % (system_fourth, system_fifth)
  # Target system on /data partition
  target_system_on_data = "/dev/block/platform/msm_sdcc.1/by-name/userdata /raw-data ext4 %s %s\n" % (system_fourth, system_fifth)

  has_cache_line = False

  f = c.open_file(directory, 'fstab.qcom', c.WRITE)
  for line in lines:
    if re.search(r"^/dev[a-zA-Z0-9/\._-]+\s+/system\s+.*$", line):
      if '/raw-system' in partition_config.target_cache:
        c.write(f, target_cache_on_system)
      else:
        c.write(f, system)

    elif re.search(r"^/dev[^\s]+\s+/cache\s+.*$", line):
      if '/raw-cache' in partition_config.target_system:
        c.write(f, target_system_on_cache)
      else:
        c.write(f, cache)

      has_cache_line = True

    elif re.search(r"^/dev[^\s]+\s+/data\s+.*$", line):
      if '/raw-data' in partition_config.target_system:
        c.write(f, target_system_on_data)
      else:
        c.write(f, data)

    else:
      c.write(f, line)

  if not has_cache_line:
    if '/raw-cache' in partition_config.target_system:
      c.write(f, target_system_on_cache)
    else:
      c.write(f, cache)

  f.close()

def modify_init_target_rc(directory):
  lines = c.get_lines_from_file(directory, 'init.target.rc')

  previous_line = ""

  f = c.open_file(directory, 'init.target.rc', c.WRITE)
  for line in lines:
    if re.search(r"^\s+wait\s+/dev/.*/cache.*$", line):
      c.write(f, re.sub(r"^", "#", line))

    elif re.search(r"^\s+check_fs\s+/dev/.*/cache.*$", line):
      c.write(f, re.sub(r"^", "#", line))

    elif re.search(r"^\s+mount\s+ext4\s+/dev/.*/cache.*$", line):
      c.write(f, re.sub(r"^", "#", line))

    elif re.search(r"^\s+mount_all\s+fstab.qcom.*$", line) and \
        re.search(r"^on\s+fs_selinux.*$", previous_line):
      c.write(f, line)
      c.write(f, c.whitespace(line) + "exec /sbin/busybox-static sh /init.multiboot.mounting.sh\n")

    elif re.search(r"^.*setprop.*selinux.reload_policy.*$", line):
      c.write(f, re.sub(r"^", "#", line))

    else:
      c.write(f, line)

    previous_line = line

  f.close()

def modify_MSM8960_lpm_rc(directory):
  lines = c.get_lines_from_file(directory, 'MSM8960_lpm.rc')

  f = c.open_file(directory, 'MSM8960_lpm.rc', c.WRITE)
  for line in lines:
    if re.search(r"^\s+mount.*/cache.*$", line):
      c.write(f, re.sub(r"^", "#", line))

    else:
      c.write(f, line)

  f.close()

def patch_ramdisk(directory, partition_config):
  modify_init_rc(directory)
  modify_init_qcom_rc(directory)
  modify_fstab(directory, partition_config)
  modify_init_target_rc(directory)
  modify_MSM8960_lpm_rc(directory)
