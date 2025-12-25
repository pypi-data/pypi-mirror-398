def cleanSkins(context):
    """Execute the 'to_123' profile that will clean skins."""
    context.runAllImportStepsFromProfile('profile-plonetheme.imioapps:to_123')


def installCollectiveFontawesome(context):
    """Install collective.fontawesome dependency."""
    context.runAllImportStepsFromProfile('profile-collective.fontawesome:default')
