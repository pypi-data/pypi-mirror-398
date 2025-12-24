<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:jp="http://www.jpo.go.jp"
    xmlns:my="my"
    exclude-result-prefixes="jp my">

    <!-- procedure-params -->
    <xsl:template
        match="
        procedure-param[@name='law'] |
        procedure-param[@name='document-code'] |
        procedure-param[@name='document-name'] |
        procedure-param[@name='application-number'] |
        procedure-param[@name='registration-number'] |
        procedure-param[@name='international-application-number'] |
        procedure-param[@name='appeal-reference-number'] |
        procedure-param[@name='receipt-number']">
        <xsl:variable name="element" select="key('key-to-tags-table', @name, $tags-table)/@new-tag" />
        <xsl:element name="{$element}">
            <xsl:value-of select="." />
        </xsl:element>
    </xsl:template>

    <xsl:template
        match="
        procedure-param[@name='file-reference-id'] |
        procedure-param[@name='reference-id']">
        <xsl:variable name="element" select="key('key-to-tags-table', @name, $tags-table)/@new-tag" />
        <xsl:if test=". != ''">
            <xsl:element name="{$element}">
                <xsl:value-of select="." />
            </xsl:element>
        </xsl:if>
    </xsl:template>

    <!-- YYYYMMDD HHMMSS to UNIX epoch time in UTC -->
    <xsl:template
        match="procedure-param[@name='submission-date'] | procedure-param[@name='dispatch-date'] ">
        <xsl:if test="./date != '' and ./time != ''">
            <xsl:variable name="s"
                select="
                substring(date, 1, 4) || '-' ||
                substring(date, 5, 2) || '-' ||
                substring(date, 7, 2) || 'T' ||
                substring(time, 1, 2) || ':' ||
                substring(time, 3, 2) || ':' ||
                substring(time, 5, 2)" />
            <!-- JST -> UTC -> epoch time -->
            <xsl:variable name="srDate" select="xs:dateTime($s)" as="xs:dateTime" />
            <xsl:variable name="unixEpoch" select="xs:dateTime('1970-01-01T00:00:00')"
                as="xs:dateTime" />
            <xsl:variable name="delta" select="xs:dayTimeDuration($srDate - $unixEpoch)"
                as="xs:dayTimeDuration" />
            <xsl:variable name="deltaUTC" select="$delta - xs:dayTimeDuration('PT9H')"
                as="xs:dayTimeDuration" />
            <xsl:variable name="epoch" select="$deltaUTC div xs:dayTimeDuration('PT1S')" />
            <xsl:element name="SRDate">
                <xsl:value-of select="$epoch" />
            </xsl:element>
        </xsl:if>
    </xsl:template>

    <!-- metadata -->
    <xsl:template match="metadata">
        <xsl:apply-templates select="id" />
        <xsl:apply-templates select="kind" />
        <xsl:apply-templates select="ext" />
    </xsl:template>

    <xsl:template match="id | kind | ext">
        <xsl:variable name="element"
            select="key('key-to-tags-table', name(.), $tags-table)/@new-tag" />
        <xsl:element name="{$element}">
            <xsl:value-of select="my:normalize-text(.)" />
        </xsl:element>
    </xsl:template>

    <xsl:function name="my:normalize-text" as="xs:string">
        <xsl:param name="input" as="xs:string" />
        <xsl:value-of select="translate(normalize-space($input), '　', '')" />
    </xsl:function>

    <xsl:function name="my:normalize-name" as="xs:string">
        <xsl:param name="input" as="xs:string" />
        <xsl:value-of select="translate($input, '　▲▼', '')" />
    </xsl:function>

    <xsl:template name="zero-pad">
        <xsl:param name="number" />
        <xsl:param name="length" select="4" />
        <xsl:variable name="padded" select="'0000' || $number" />
        <xsl:value-of select="substring($padded, string-length($padded) - $length + 1)" />
    </xsl:template>

    <xsl:key name="key-to-tags-table" match="item" use="@tag" />
    <xsl:variable name="tags-table">
        <item tag="law" new-tag="Law" />
        <item tag="application-number" new-tag="ApplicationNumber" />
        <item tag="registration-number" new-tag="RegistrationNumber" />
        <item tag="international-application-number" new-tag="IntlAppNumber" />
        <item tag="receipt-number" new-tag="ReceiptNumber" />
        <item tag="appeal-reference-number" new-tag="AppealReferenceNumber" />
        <item tag="document-name" new-tag="DocumentName" />
        <item tag="id" new-tag="DocumentId" />
        <item tag="document-code" new-tag="DocumentCode" />
        <item tag="kind" new-tag="DocumentKind" />
        <item tag="ext" new-tag="DocumentExt" />
        <item tag="reference-id" new-tag="FileReferenceNumber" />
        <item tag="file-reference-id" new-tag="FileReferenceNumber" />
        <item tag="applicants" new-tag="Applicants" new-tag-sub="Applicant" />
        <item tag="inventors" new-tag="Inventors" new-tag-sub="Inventor" />
        <item tag="applicant" new-tag="Applicant" />
        <item tag="inventor" new-tag="Inventor" />
        <item tag="m-dispatch-applicant-group" json-key="Applicants" />
        <item tag="m-dispatch-attorney-group" json-key="Agents" />
    </xsl:variable>

    <!-- override build-in template for text and attribute nodes. -->
    <xsl:template match="text()|@*">
        <!-- <xsl:value-of select="normalize-space(.)"/> -->
    </xsl:template>
</xsl:stylesheet>