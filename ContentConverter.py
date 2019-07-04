import datetime
import orgparse
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

renderedContentDictionary = {}

class RenderedContentMetadata:
    def __init__(self, contentFile, contentPath, renderedFilePath):
        self.contentFile = contentFile
        self.contentPath = contentPath
        self.renderedFilePath = renderedFilePath

        # Properties inherited from the org properties. Code-queried properties added by default
        self.properties = {}
        # Set a default date far in the past which is obviously wrong (so you'll fix your data)
        self.properties["PUBLISHED"] = datetime.datetime(2000, 1, 1)
        self.properties["TITLE"] = None
        
def metadataGetOrgProperties(metadata):
    if not os.path.exists(metadata.contentFile):
        print('ERROR: Could not find associated org file "{}" for content file "{}"\n'
              '\tThe file will be missing necessary metadata'.format(metadata.contentFile,
                                                                     metadata.renderedFilePath))
        return

    orgRoot = orgparse.load(metadata.contentFile)
    for node in orgRoot[1:]:
        for property, value in node.properties.items():
            if property == "PUBLISHED":
                metadata.properties[property] = datetime.datetime.strptime(value, '%Y-%m-%d')
            else:
                metadata.properties[property] = value
        # Set TITLE as the first node if it's not a property
        if not metadata.properties["TITLE"]:
            metadata.properties["TITLE"] = node.heading

def updateRenderedCache():
    global renderedCache
    global renderedContentDictionary
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
                
                # This sucks
                contentFile = "{}/{}.{}".format(contentDirectory, contentPath, "org")
                metadata = RenderedContentMetadata(contentFile, contentPath, renderedFile)
                metadataGetOrgProperties(metadata)
                
                renderedContentDictionary[contentPath] = metadata

"""
Interface
"""

def getAllPostsList():
    allPosts = []
    for key, value in renderedContentDictionary.items():
        # Hide folders and files with '_hidden' (they can still be retrieved though)
        if '_hidden' in key:
            continue
        
        allPosts.append(key)

    return allPosts

def getRenderedContentDictionary():
    return renderedContentDictionary
                
def getRenderedBody(contentPath):
    body = None
    if contentPath in renderedContentDictionary:
        renderedFilename = renderedContentDictionary[contentPath].renderedFilePath
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
