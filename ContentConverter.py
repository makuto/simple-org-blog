import os
import subprocess

contentDirectory = "content"
renderedDirectory = "renderedContent"

# Pairs of extension, pandoc read type
# HTML->HTML is essentially a copy, with some pandoc sugar added (see pandoc docs)
convertableContentTypes = [(".org", "org"), (".html", "html")]
contentExtensions = []
for contentType in convertableContentTypes:
    contentExtensions.append(contentType[0])
contentExtensions = tuple(contentExtensions)
    
renderedContentTypes = [(".html", "html")]
defaultRenderedTypeIndex = 0
renderedContentExtensions = []
for contentType in renderedContentTypes:
    renderedContentExtensions.append(contentType[0])
renderedContentExtensions = tuple(renderedContentExtensions)
    
def getContentReadType(contentFilename):
    contentExtension = contentFilename[contentFilename.rfind("."):]
    for contentType in convertableContentTypes:
        if contentExtension == contentType[0]:
            return contentType[1]

# Strip the content directory
def getContentLocalName(contentFilename):
    return contentFilename[len(contentDirectory):]

# Strip the rendered directory
def getRenderedLocalName(filename):
    return filename[len(renderedDirectory):]

def stripExtension(filename):
    return filename[:filename.rfind(".")]

def contentFilenameToRenderedFilename(contentFilename):
    return "{}{}{}".format(renderedDirectory,
                           stripExtension(getContentLocalName(contentFilename)),
                           renderedContentTypes[defaultRenderedTypeIndex][0])

def renderContent(contentFilename):
    # Content modified recently; render it
    print("\tRendering {}".format(contentFilename))
    
    outputFilename = contentFilenameToRenderedFilename(contentFilename)

    # Make subdirectory if necessary
    if not os.path.exists(os.path.dirname(outputFilename)):
            os.makedirs(os.path.dirname(outputFilename))
    
    # TODO: Support multiple output formats?
    subprocess.run(["pandoc",
                    "-r", getContentReadType(contentFilename),
                    "-w", renderedContentTypes[defaultRenderedTypeIndex][1],
                    "-o", outputFilename, contentFilename])

# List of all content files
contentCache = []

renderedCache = []

renderedDictionary = {}

def updateRenderedCache():
    global renderedCache
    global renderedDictionary
    renderedCache = []
    # Get all rendered files
    for root, dirs, files in os.walk(renderedDirectory):
        for file in files:
            if file.endswith(renderedContentExtensions):
                renderedFile = os.path.join(root, file)
                renderedCache.append(renderedFile)
                # The path actually used to look up the content (strip '/' from front)
                contentPath = getRenderedLocalName(stripExtension(renderedFile))[1:]
                print("\t'{}' = '{}'".format(contentPath, renderedFile))
                # No use for the value yet, we just want fast key lookups
                renderedDictionary[contentPath] = renderedFile

"""
Interface
"""

def getAllPostsList():
    allPosts = []
    for key, value in renderedDictionary.items():
        # Hide folders and files with '_hidden' (they can still be retrieved though)
        if '_hidden' in key:
            continue
        
        allPosts.append(key)

    return allPosts
                
def getRenderedBody(contentPath):
    body = None
    if contentPath in renderedDictionary:
        renderedFilename = renderedDictionary[contentPath]
        renderedFile = open(renderedFilename)
        body = renderedFile.readlines()
        body = "".join(body)
        renderedFile.close()
    return body

def checkForContentChange():
    global contentCache
    
    print("Checking for content updates...")
    
    # Get all content files
    contentCache = []
    for root, dirs, files in os.walk(contentDirectory):
        # I'm going to use git to version content, so ignore the .git dir
        if '.git' in root:
            continue

        for file in files:
            if file.endswith(contentExtensions):
                contentCache.append(os.path.join(root, file))

    updateRenderedCache()

    numRenderedFiles = 0

    # Compare timestamps to determine which files need regeneration
    for contentFilename in contentCache:
        contentModified = os.path.getmtime(contentFilename)
        contentLocalName = getContentLocalName(contentFilename)

        renderedFileFound = False
        for renderedFile in renderedCache:
            if stripExtension(renderedFile[len(renderedDirectory):]) != stripExtension(contentLocalName):
                continue

            renderedFileFound = True
            renderedModified = os.path.getmtime(renderedFile)

            # Modified content
            if contentModified > renderedModified:
                renderContent(contentFilename)
                numRenderedFiles += 1

        # New content file
        if not renderedFileFound:
            renderContent(contentFilename)
            numRenderedFiles += 1

    # We generated new content; make sure the cache is up-to-date
    if numRenderedFiles:
        updateRenderedCache()
    
    print("Checking for content updates done. Rendered {} files".format(numRenderedFiles))
