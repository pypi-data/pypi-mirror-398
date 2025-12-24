<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="3.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:jp="http://www.jpo.go.jp">

    <!-- 出願番号10桁と文書名を、特願YYYY-NNNNNN 文書名 のように変換する-->
    <xsl:template name="html-title">
        <xsl:param name="law" /> <!-- 法律の種別 1:特、2:実,3:意,4:商-->
        <xsl:param name="application-number" /><!-- 出願番号10桁 -->
        <xsl:param name="document-name" /> <!-- 文書名 -->

        <xsl:choose>
            <xsl:when test="$law = '1'">
                <xsl:value-of select="'特願'" />
            </xsl:when>
            <xsl:when test="$law = '2'">
                <xsl:value-of select="'実願'" />
            </xsl:when>
            <xsl:when test="$law = '3'">
                <xsl:value-of select="'意願'" />
            </xsl:when>
            <xsl:when test="$law = '4'">
                <xsl:value-of select="'商願'" />
            </xsl:when>
        </xsl:choose>
        <xsl:value-of select="substring($application-number, 1, 4)" />
        <xsl:text>-</xsl:text>
        <xsl:value-of select="substring($application-number, 5, 6)" />
        <xsl:text>号 </xsl:text>
        <xsl:value-of select="$document-name" />
    </xsl:template>
</xsl:stylesheet>
