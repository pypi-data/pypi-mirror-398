<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:tei="http://www.tei-c.org/ns/1.0" version="2.0">
    <xsl:output method="html" encoding="UTF-8" indent="yes"/>

    <!-- Template for the root element -->
    <xsl:template match="/">
        <html>
            <head>
                <title>Dummy XSLT Transformation</title>
            </head>
            <body>
                <h1>Dummy XSLT Transformation</h1>
                <xsl:apply-templates/>
            </body>
        </html>
    </xsl:template>

    <!-- Template for the TEI Header element -->
    <xsl:template match="tei:teiHeader">
        <div>
            <h2>TEI Header</h2>
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <!-- Template for the Title element -->
    <xsl:template match="tei:title">
        <h3>Title: <xsl:value-of select="."/></h3>
    </xsl:template>

    <!-- Template for the Abstract element -->
    <xsl:template match="tei:abstract">
        <div>
            <h3>Abstract</h3>
            <p><xsl:value-of select="."/></p>
        </div>
    </xsl:template>

    <!-- Template for the Paragraph element -->
    <xsl:template match="tei:p">
        <p><xsl:value-of select="."/></p>
    </xsl:template>

    <!-- Template for all other elements -->
    <xsl:template match="node() | @*">
        <xsl:apply-templates/>
    </xsl:template>
</xsl:stylesheet>