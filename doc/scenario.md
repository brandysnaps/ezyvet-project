# Scenario

The Platform team is getting repeated requests from various development and conversion teams with the requirement of being able to launch an AWS server to complete processing tasks.

## Required Functionality

- ✅ The ability to specify minimum and maximum number of CPU's
- ✅ The ability to specify minimum and maximum amount of RAM
- ✅ The ability to specify spot or on-demand instance types
- ✅ The ability to set AWS region to launch in.

## Desired Outcome

- ✅ The solution should optimise for cost as its number one priority.
- ✅ The solution should use sensible defaults where the above options are not set
- ✅ The solution will be executed as part of various CI pipelines so should be non interactive and able to be retro fitted to existing scripts and infrastructure as code repos
- ✅ The solution will be used to replace hard coded instance types which have been selected for CPU and RAM attributes but are not necessarily the most cost effective option

## Stretch Goals

- ❌ Solution should be auto healing
- ✅ Solution should be future proof - i.e. as new instance types are added by AWS they will be used if appropriate