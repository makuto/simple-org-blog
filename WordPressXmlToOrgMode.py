"""
Dead stupid converter for Wordpress XML dumps. 

To get a dump of your Wordpress blog, go to "My Sites"->Configure->Settings->Export->Export your Content. 
Extract that and feed this the .xml's filename
"""

import xml.dom.minidom as minidom
import os

wordpressFilename = "/home/macoy/Downloads/au79games.wordpress.com-2019-03-14-02_02_05-kzxvzzu42xryynuzqbm9c23f7gtdtyk3/au79games.wordpress.com-2019-03-14-02_02_03/au79games.wordpress.2019-03-14.001.xml"

outputDir = "content/gamedev"

contentFormat = "<h1>{}</h1><p>{}</p>"

def titleToFilename(title):
    filename = ""
    for char in title:
        if char.isalnum():
            filename += char

    return filename

def main():
    domTree = minidom.parse(wordpressFilename)
    collection = domTree.documentElement
    items = collection.getElementsByTagName("item")
    
    for item in items:
        # Ignore anything which isn't a post
        if not item.getElementsByTagName("wp:post_type")[0].childNodes[0].data == "post":
            continue

        title = item.getElementsByTagName("title")[0].childNodes[0].data
        content = item.getElementsByTagName("content:encoded")[0].childNodes[0].data
        
        print(title)
        print(titleToFilename(title))
        print(content)

        # Write to .html
        outputFilename = "{}/{}.html".format(outputDir, titleToFilename(title))
        if not os.path.exists(os.path.dirname(outputFilename)):
            os.makedirs(os.path.dirname(outputFilename))
        outFile = open(outputFilename, "w")
        outFile.write(contentFormat.format(title, content))
        outFile.close()
        print("Wrote {}".format(outputFilename))

if __name__ == "__main__":
    main()
