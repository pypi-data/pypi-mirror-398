<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:jp="http://www.jpo.go.jp"
    xmlns:my="my"
    exclude-result-prefixes="my jp">

    <!-- 発明者、出願人-->
    <xsl:template match="jp:inventors | jp:applicants">
        <xsl:variable name="element"
            select="key('key-to-tags-table', local-name(.), $tags-table)/@new-tag" />
        <xsl:variable name="sub-element"
            select="key('key-to-tags-table', local-name(.), $tags-table)/@new-tag-sub" />
        <xsl:element name="{$element}">
            <xsl:for-each select=".//jp:name">
                <xsl:element name="{$sub-element}">
                    <xsl:value-of select="my:normalize-name(.)" />
                </xsl:element>
            </xsl:for-each>
        </xsl:element>
    </xsl:template>

    <!-- 代理人, 選任した代理人 -->
    <xsl:template match="jp:agents">
        <xsl:element name="Agents">
            <xsl:for-each select="//jp:agents//jp:name">
                <xsl:element name="Agent">
                    <xsl:value-of select="my:normalize-name(.)" />
                </xsl:element>
            </xsl:for-each>
            <xsl:for-each select="//jp:attorney-change-article//jp:name">
                <xsl:element name="Agent">
                    <xsl:value-of select="my:normalize-name(.)" />
                </xsl:element>
            </xsl:for-each>
        </xsl:element>
    </xsl:template>
</xsl:stylesheet>