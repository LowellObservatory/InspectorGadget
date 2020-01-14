import glob
from shutil import copyfile
from datetime import datetime as dt

from os import remove
from os.path import basename


def getFilenameAgeDiff(fname, now, dtfmt="%Y%j%H%M%S%f"):
    """
    NOTE: HERE 'maxage' is already in seconds! Convert before calling.
    """
    # Need to basename it to get just the actual filename and not the path
    beach = basename(fname)

    try:
        dts = dt.strptime(beach, dtfmt)
        diff = (now - dts).total_seconds()
    except Exception as err:
        # TODO: Catch the right datetime conversion error!
        print(str(err))
        # Make it "current" to not delete it
        diff = 0

    return diff


def findOldFiles(inloc, fmask, now, maxage=24., dtfmt="%Y%j%H%M%S%f"):
    """
    'maxage' is in hours
    Returns two dictionaries, one for the current (young) files and one
    for the out-of-date (old) files. Both dicts are set up the same,
    with the keys being the filenames and their values their determined age.
    """
    maxage *= 60. * 60.
    flist = sorted(glob.glob(inloc + fmask))

    goldenoldies = {}
    youngsters = {}
    for each in flist:
        diff = getFilenameAgeDiff(each, now, dtfmt=dtfmt)
        if diff > maxage:
            goldenoldies.update({each: diff})
        else:
            youngsters.update({each: diff})

    return youngsters, goldenoldies


def deleteOldFiles(fdict):
    """
    fdict should be a dictionary whose key is the filename and the
    value is that filename's determined age (in seconds)
    """
    for key in fdict:
        print("Deleting %s since it's too old (%.3f hr)" %
              (key, fdict[key]/60./60.))
        try:
            remove(key)
        except OSError as err:
            # At least see what the issue was
            print(str(err)) 


def copyStaticFilenames(cpng, lout, staticname, nstaticfiles):
    """
    cpng should be a dict, whose key is the filename and the
    value is that filename's determined age (in seconds)
    errorAge is given in hours and then converted to seconds
    """
    latestname = '%s/%s_latest.png' % (lout, staticname)

    # Since we gave it a dict we just put it into a list to make
    #   indexing below a little easier.
    clist = list(cpng.keys())
    cages = list(cpng.values())

    # Make sure we don't try to operate on an empty dict, or one too small
    if len(cpng) < nstaticfiles:
        lindex = len(cpng)
    else:
        lindex = nstaticfiles

    icount = 0
    # It's easier to do this in reverse
    for findex in range(-1*lindex, 0, 1):
        try:
            lname = "%s/%s_%03d.png" % (lout, staticname, icount)
            icount += 1
            copyfile(clist[findex], lname)
        except Exception as err:
            # TODO: Figure out the proper/specific exception
            print(str(err))
            print("WHOOPSIE! COPY FAILED")

    # Put the very last file in the last file slot
    latest = clist[-1]
    try:
        copyfile(latest, latestname)
        print("Latest file copy done!")
    except Exception as err:
        # TODO: Figure out the proper/specific exception to catch
        print(str(err))
        print("WHOOPSIE! COPY FAILED")

