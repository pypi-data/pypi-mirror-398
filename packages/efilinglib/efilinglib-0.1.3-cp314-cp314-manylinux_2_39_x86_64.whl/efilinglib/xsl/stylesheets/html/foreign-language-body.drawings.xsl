<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:jp="http://www.jpo.go.jp"
    exclude-result-prefixes="jp">

    <xsl:output method="html" encoding="utf-8" omit-xml-declaration="yes"
        doctype-public="-//W3C//DTD HTML 4.01 Transitional//EN"
        doctype-system="http://www.w3.org/TR/html4/loose.dtd" indent="yes" media-type="text/html" />

    <xsl:variable name="node" select="jp:foreign-language-body" />
    <xsl:variable name="kind-of-law" select="//jp:pat-app-doc/*/@jp:kind-of-law" />
    <xsl:include href="parts/pat_common.xsl" />

    <!-- lookup table defined in source xml. -->
    <xsl:key name="procedure-params" match="procedure-param" use="@name" />


    <xsl:template match="/root">
        <xsl:apply-templates select="jp:foreign-language-body" />
    </xsl:template>

    <!-- ====================================================================
     jp:foreign-language-body
     ====================================================================-->
    <xsl:template match="jp:foreign-language-body">
        <xsl:apply-templates select="jp:foreign-language-drawings" />
    </xsl:template>

    <!-- ====================================================================
     jp:foreign-language-drawings
     ====================================================================-->
    <!-- 外国語図面 -->
    <xsl:template match="jp:foreign-language-drawings">
        <xsl:element name="div">
            <xsl:attribute name="class" select="local-name(.)" />
            <xsl:value-of select="'【書類名】外国語図面'" />
            <xsl:apply-templates select="p" />
        </xsl:element>
    </xsl:template>
</xsl:stylesheet>