<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:jp="http://www.jpo.go.jp"
    exclude-result-prefixes="jp">

    <!-- this xslt was created with reference to pat_common.xsl
     of Internet Application Software version i5.30 provided by JPO -->


    <xsl:output method="html" encoding="utf-8" omit-xml-declaration="yes"
        doctype-public="-//W3C//DTD HTML 4.01 Transitional//EN"
        doctype-system="http://www.w3.org/TR/html4/loose.dtd" indent="yes" media-type="text/html" />

    <xsl:variable name="node" select="name(//jp:pat-app-doc/*)" />
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

                <xsl:apply-templates select="application-body" />
            </body>
        </html>
    </xsl:template>

    <!-- ====================================================================
     jp:application-a63
     ====================================================================-->
    <xsl:template match="jp:application-a63">
        <xsl:apply-templates select="jp:document-code" />
        <xsl:apply-templates select="jp:file-reference-id" />
        <xsl:apply-templates select="jp:special-mention-matter-article" />
        <xsl:apply-templates select="jp:submission-date" />
        <xsl:apply-templates select="jp:addressed-to-person" />
        <xsl:apply-templates select="jp:parent-application-article" />
        <xsl:apply-templates select="jp:ipc-article" />
        <xsl:apply-templates select="jp:inventors" />
        <xsl:apply-templates select="jp:applicants" />
        <xsl:apply-templates select="jp:trust-relation" />
        <xsl:apply-templates select="jp:agents" />
        <xsl:apply-templates select="jp:attorney-change-article" />
        <xsl:apply-templates select="jp:priority-claims" />
        <xsl:apply-templates select="jp:declaration-priority-ear-app" />
        <xsl:apply-templates select="jp:law-of-industrial-regenerate" />
        <xsl:apply-templates select="jp:payment-years" />
        <xsl:apply-templates select="jp:share-rate" />
        <xsl:apply-templates select="jp:charge-article" />
        <xsl:apply-templates select="jp:dtext" />
        <xsl:apply-templates select="jp:submission-object-list-article" />
        <xsl:apply-templates select="jp:proof-necessity" />
        <xsl:apply-templates select="jp:rule-outside-item-article" />
    </xsl:template>

    <!-- ====================================================================
     jp:application-a631
     ====================================================================-->
    <xsl:template match="jp:application-a631">
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
        <xsl:apply-templates select="jp:notice-contents-group" />
        <xsl:apply-templates select="jp:dtext" />
        <xsl:apply-templates select="jp:submission-object-list-article" />
        <xsl:apply-templates select="jp:rule-outside-item-article" />
    </xsl:template>

    <!-- ====================================================================
     jp:application-a632
     ====================================================================-->
    <xsl:template match="jp:application-a632">
        <xsl:apply-templates select="jp:document-code" />
        <xsl:apply-templates select="jp:file-reference-id" />
        <xsl:apply-templates select="jp:submission-date" />
        <xsl:apply-templates select="jp:addressed-to-person" />
        <xsl:apply-templates select="jp:indication-of-case-article" />
        <xsl:apply-templates select="jp:inventors" />
        <xsl:apply-templates select="jp:applicants" />
        <xsl:apply-templates select="jp:trust-relation" /><!--Y07M04出願人名義変更追加対応-->
        <xsl:apply-templates select="jp:agents" />
        <xsl:apply-templates select="jp:attorney-change-article" />
        <xsl:apply-templates select="jp:law-of-industrial-regenerate" />
        <xsl:apply-templates select="jp:payment-years" />
        <xsl:apply-templates select="jp:share-rate" />
        <xsl:apply-templates select="jp:charge-article" />
        <xsl:apply-templates select="jp:dispatch-number" />
        <xsl:apply-templates select="jp:notice-contents-group" />
        <xsl:apply-templates select="jp:dtext" />
        <xsl:apply-templates select="jp:submission-object-list-article" />
        <xsl:apply-templates select="jp:rule-outside-item-article" />
    </xsl:template>

    <!-- ====================================================================
     jp:application-a633
     ====================================================================-->
    <xsl:template match="jp:application-a633">
        <xsl:apply-templates select="jp:document-code" />
        <xsl:apply-templates select="jp:file-reference-id" />
        <xsl:apply-templates select="jp:submission-date" />
        <xsl:apply-templates select="jp:addressed-to-person" />
        <xsl:apply-templates select="jp:indication-of-case-article" />
        <xsl:apply-templates select="jp:applicants" />
        <xsl:apply-templates select="jp:agents" />
        <xsl:apply-templates select="jp:dispatch-number" />
        <xsl:apply-templates select="jp:dtext" />
        <xsl:apply-templates select="jp:submission-object-list-article" />
        <xsl:apply-templates select="jp:rule-outside-item-article" />
    </xsl:template>

    <!-- ====================================================================
     jp:application-a634
     ====================================================================-->
    <xsl:template match="jp:application-a634">
        <xsl:apply-templates select="jp:document-code" />
        <xsl:apply-templates select="jp:file-reference-id" />
        <xsl:apply-templates select="jp:submission-date" />
        <xsl:apply-templates select="jp:addressed-to-person" />
        <xsl:apply-templates select="jp:indication-of-case-article" />
        <xsl:apply-templates select="jp:applicants" />
        <xsl:apply-templates select="jp:agents" />
        <xsl:apply-templates select="jp:dtext" />
        <xsl:apply-templates select="jp:submission-object-list-article" />
        <xsl:apply-templates select="jp:rule-outside-item-article" />
    </xsl:template>

    <!-- ====================================================================
     jp:application-a635
     ====================================================================-->
    <xsl:template match="jp:application-a635">
        <xsl:apply-templates select="jp:document-code" />
        <xsl:apply-templates select="jp:file-reference-id" />
        <xsl:apply-templates select="jp:submission-date" />
        <xsl:apply-templates select="jp:addressed-to-person" />
        <xsl:apply-templates select="jp:indication-of-case-article" />
        <xsl:apply-templates select="jp:applicants" />
        <xsl:apply-templates select="jp:agents" />
        <xsl:apply-templates select="jp:notice-contents-group" />
        <xsl:apply-templates select="jp:dtext" />
        <xsl:apply-templates select="jp:submission-object-list-article" />
        <xsl:apply-templates select="jp:rule-outside-item-article" />
    </xsl:template>

</xsl:stylesheet>