<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:jp="http://www.jpo.go.jp"
    exclude-result-prefixes="jp">

    <xsl:template match="jp:dispatch-control-article">
        <xsl:element name="div">
            <xsl:attribute name="class">
                <xsl:value-of select="local-name(.)" />
            </xsl:attribute>

            <xsl:element name="div"> 整理番号: <xsl:value-of select="jp:file-reference-id" />
            </xsl:element>
            <xsl:element name="div"> 発送番号: <xsl:value-of select="jp:dispatch-number" />
            </xsl:element>
            <xsl:element name="div"> 発送日 : <xsl:value-of select="jp:dispatch-date/jp:date" />
            </xsl:element>
        </xsl:element>
        <xsl:element name="hr" />
    </xsl:template>
</xsl:stylesheet>
