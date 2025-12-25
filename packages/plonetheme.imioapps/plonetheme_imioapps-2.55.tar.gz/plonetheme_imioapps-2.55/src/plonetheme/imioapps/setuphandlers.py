def isNotplonemeetingskinProfile(context):
    return context.readDataFile("plonemeetingskin_marker.txt") is None


def plonemeetingskinSetupVarious(context):

    if isNotplonemeetingskinProfile(context):
        return

    # site = context.getSite()

    # maybe one day we will have to add some lines here above...
