<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:jp="http://www.jpo.go.jp"
    xmlns:my="my"
    exclude-result-prefixes="jp">

    <!-- cpy-ntc-pat-e, cpy-ntc-pat-e-rn 共用 -->

    <xsl:output method="xml" encoding="utf-8" indent="yes" />
    <xsl:import href="parts/common.xsl" />
    <xsl:import href="parts/dispatched-docs.common.xsl" />

    <xsl:template match="/root">
        <xsl:element name="document">
            <xsl:apply-templates select="metadata" />
            <xsl:apply-templates select="procedure-params/procedure-param" />
            <xsl:apply-templates select="//jp:m-applicant-and-attorneys" />
            <xsl:apply-templates select="//jp:drafting-body" />
            <xsl:apply-templates select="//jp:article-group" />
        </xsl:element>
    </xsl:template>

    <!-- 拒絶理由 -->
    <xsl:template match="jp:drafting-body">
        <xsl:if test="//jp:drafting-body != ''">
            <xsl:element name="Prosecution">
                <xsl:value-of select="my:normalize-text(//jp:drafting-body)" />
            </xsl:element>
        </xsl:if>
    </xsl:template>

    <!-- 拒絶理由コード -->
    <xsl:template match="jp:article-group">
        <xsl:element name="RejectionCodes">
            <xsl:for-each select="jp:article">
                <xsl:element name="RejectionCode">
                    <xsl:value-of select="." />
                </xsl:element>
            </xsl:for-each>
        </xsl:element>
    </xsl:template>
</xsl:stylesheet>