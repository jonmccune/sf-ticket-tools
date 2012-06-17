sf-ticket-tools
===============

Scripts to take exported Redmine issues and import them into a SourceForge API v2.0 project

# Author: Jon McCune <jonmccune@gmail.com>
# License: BSD-style
# Significant help from the example at:
# https://sourceforge.net/p/forge/documentation/API%20-%20Beta/
# Thanks also to the #sourceforge IRC channel

==> ticket-importer.py <==

This script will process a .CSV file containing issues exported from
Redmine 1.0.3 (have not tried with other versions; likely to work
with little or no modification), and use the SourceForge API v2.0
Beta to import the issues into a SourceForge project's issue
tracker.


==> ticket-updater.py <==

# This script will update the labels attached to existing issues in
# the SourceForge v2.0 API Beta.  This is mildly tricky because the API
# clobbers existing labels.  Our basic operation is thus to fetch the
# existing labels, extend the list with new ones of interest, and then
# assign the new labels.

