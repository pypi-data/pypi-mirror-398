<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:jp="http://www.jpo.go.jp"
    exclude-result-prefixes="jp">

    <!-- this xslt was created with reference to pat-rspn.xsl
     of Internet Application Software version i5.30 provided by JPO -->


    <xsl:output name="html_out" method="html" encoding="utf-8" omit-xml-declaration="yes"
        doctype-public="-//W3C//DTD HTML 4.01 Transitional//EN"
        doctype-system="http://www.w3.org/TR/html4/loose.dtd" indent="yes" media-type="text/html" />

    <xsl:variable name="node" select="name(//jp:pat-rspns/*)" />
    <xsl:variable name="kind-of-law" select="//jp:pat-rspns/*/@jp:kind-of-law" />

    <xsl:include href="parts/pat_common.xsl" />
    <xsl:include href="common.xsl" />

    <!-- lookup table defined in source xml. -->
    <xsl:key name="procedure-params" match="procedure-param" use="@name" />

    <xsl:template match="/root">
        <html>
            <head>
                <title>
                    <xsl:call-template name="html-title">
                        <xsl:with-param name="law"
                            select="/root/procedure-params/procedure-param[@name='law']" />
                        <xsl:with-param name="application-number"
                            select="/root/procedure-params/procedure-param[@name='application-number']" />
                        <xsl:with-param name="document-name"
                            select="/root/procedure-params/procedure-param[@name='document-name']" />
                    </xsl:call-template>
                </title>
                <style> body { font-family: Hiragino Kaku Gothic ProN, Meiryo, Ricty Diminished,
                    Monaco, Consolas, Courier New, Courier, monospace, sans-serif; width: 40em; } p
                    { margin-top: 5px; margin-bottom: 5px; } </style>
            </head>
            <body>
                <xsl:element name="div">
                    <xsl:attribute name="class">response</xsl:attribute>
                    <xsl:apply-templates select="jp:pat-rspns" />
                </xsl:element>
            </body>
        </html>
    </xsl:template>

    <!-- ====================================================================
     jp:response-a53 | jp:response-a59
     ====================================================================-->
    <xsl:template match="jp:response-a53 | jp:response-a59">
        <xsl:apply-templates select="jp:document-code" />
        <xsl:apply-templates select="jp:file-reference-id" />
        <xsl:apply-templates select="jp:submission-date" />
        <xsl:apply-templates select="jp:addressed-to-person" />
        <xsl:apply-templates select="jp:indication-of-case-article" />
        <xsl:apply-templates select="jp:proof-necessity" />
        <xsl:apply-templates select="jp:applicants" />
        <xsl:apply-templates select="jp:agents" />
        <xsl:apply-templates select="jp:dispatch-number" />
        <xsl:apply-templates select="jp:dispatch-date" />
        <xsl:apply-templates select="jp:opinion-contents-article"/>
        <xsl:apply-templates select="jp:proof-means" />
        <xsl:apply-templates select="jp:dtext" />
        <xsl:apply-templates select="jp:submission-object-list-article" />
        <xsl:apply-templates select="jp:rule-outside-item-article" />
    </xsl:template>

</xsl:stylesheet>