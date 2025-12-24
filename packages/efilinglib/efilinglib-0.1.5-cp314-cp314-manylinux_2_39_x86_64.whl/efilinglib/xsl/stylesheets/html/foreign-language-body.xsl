<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:jp="http://www.jpo.go.jp"
    exclude-result-prefixes="jp">

    <!-- this xslt was created with reference to foreign-language-body.xsl
     of Internet Application Software version i5.30 provided by JPO -->

    <xsl:output method="html" encoding="utf-8" omit-xml-declaration="yes"
        doctype-public="-//W3C//DTD HTML 4.01 Transitional//EN"
        doctype-system="http://www.w3.org/TR/html4/loose.dtd" indent="yes" media-type="text/html" />

    <xsl:variable name="node" select="jp:foreign-language-body" />
    <xsl:variable name="kind-of-law" select="//jp:pat-app-doc/*/@jp:kind-of-law" />
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
                    <xsl:attribute name="class">application</xsl:attribute>
                    <xsl:apply-templates select="jp:pat-app-doc" />
                </xsl:element>
                <xsl:apply-templates select="jp:foreign-language-body" />
            </body>
        </html>
    </xsl:template>

    <!-- ====================================================================
     jp:foreign-language-body
     ====================================================================-->
    <xsl:template match="jp:foreign-language-body">
        <xsl:apply-templates select="jp:foreign-language-description" />
        <xsl:apply-templates select="jp:foreign-language-claims" />
        <xsl:apply-templates select="jp:foreign-language-abstract" />
        <xsl:apply-templates select="jp:foreign-language-drawings" />
    </xsl:template>

    <!-- ====================================================================
     jp:foreign-language-claims
     ====================================================================-->
    <!-- 外国語請求の範囲 -->
    <xsl:template match="jp:foreign-language-claims">
        <xsl:element name="div">
            <xsl:attribute name="class" select="local-name(.)" />
            <xsl:element name="div">
                <xsl:value-of select="'【書類名】外国語特許請求の範囲'" />
            </xsl:element>
            <xsl:apply-templates select="p" />
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
     jp:foreign-language-description
     ====================================================================-->
    <!-- 外国語明細書 -->
    <xsl:template match="jp:foreign-language-description">
        <xsl:element name="div">
            <xsl:attribute name="class" select="local-name(.)" />
            <xsl:element name="div">
                <xsl:value-of select="'【書類名】外国語明細書'" />
            </xsl:element>
            <xsl:apply-templates select="p" />
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
     jp:foreign-language-drawings
     ====================================================================-->
    <!-- 外国語図面 -->
    <xsl:template match="jp:foreign-language-drawings">
        <xsl:element name="div">
            <xsl:attribute name="class" select="local-name(.)" />
            <xsl:element name="div">
                <xsl:value-of select="'【書類名】外国語図面'" />
            </xsl:element>
            <xsl:apply-templates select="p" />
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
     jp:foreign-language-abstract
     ====================================================================-->
    <!-- 外国語要約書 -->
    <xsl:template match="jp:foreign-language-abstract">
        <xsl:element name="div">
            <xsl:attribute name="class" select="local-name(.)" />
            <xsl:element name="div">
                <xsl:value-of select="'【書類名】外国語要約書'" />
            </xsl:element>
            <xsl:apply-templates select="p" />
        </xsl:element>
    </xsl:template>

</xsl:stylesheet>