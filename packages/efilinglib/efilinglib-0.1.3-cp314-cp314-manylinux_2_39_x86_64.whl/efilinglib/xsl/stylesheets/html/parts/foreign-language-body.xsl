<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xs="http://www.w3.org/2001/XMLSchema"
                xmlns:jp="http://www.jpo.go.jp"
                xmlns:lookup="lookup">
                
    <!-- this xslt was created with reference to foreign-language-body.xsl
         of Internet Application Software version i5.30 provided by JPO -->
    
    <xsl:key name="image-table" match="images/image" use="@orig"/>
    
    <xsl:template match="jp:foreign-language-body">
        <xsl:apply-templates select="jp:foreign-language-description" />
        <xsl:apply-templates select="jp:foreign-language-claims" />
        <xsl:apply-templates select="jp:foreign-language-abstract" />
        <xsl:apply-templates select="jp:foreign-language-drawings" />
    </xsl:template>
    
    <!-- 外国語請求の範囲 -->
    <xsl:template match="jp:foreign-language-claims">
        <xsl:element name="div">
            <xsl:attribute name="class" select="local-name(.)"/> 
            <xsl:element name="div">
                <xsl:attribute name="class" select="'document-tag'"/>
                <xsl:value-of select="'【書類名】外国語特許請求の範囲'" />
            </xsl:element>
            <xsl:apply-templates select="p" />
        </xsl:element>
    </xsl:template>
    
    <!-- 外国語明細書 -->
    <xsl:template match="jp:foreign-language-description">
        <xsl:element name="div">
            <xsl:attribute name="class" select="local-name(.)"/> 
            <xsl:element name="div">
                <xsl:attribute name="class" select="'document-tag'"/>
                <xsl:value-of select="'【書類名】外国語明細書'" />
            </xsl:element>
            <xsl:apply-templates select="p" />
        </xsl:element>
    </xsl:template>
    
    <!-- 外国語図面 -->
    <xsl:template match="jp:foreign-language-drawings">
        <xsl:element name="div">
            <xsl:attribute name="class" select="local-name(.)"/> 
            <xsl:element name="div">
                <xsl:attribute name="class" select="'document-tag'"/>
                <xsl:value-of select="'【書類名】外国語図面'" />
            </xsl:element>
            <xsl:apply-templates select="p" />
        </xsl:element>
    </xsl:template>
    
    <!-- 外国語要約書 -->
    <xsl:template match="jp:foreign-language-abstract">
        <xsl:element name="div">
            <xsl:attribute name="class" select="local-name(.)"/> 
            <xsl:element name="div">
                <xsl:attribute name="class" select="'document-tag'"/>
                <xsl:value-of select="'【書類名】外国語要約書'" />
            </xsl:element>
            <xsl:apply-templates select="p" />
        </xsl:element>
    </xsl:template>
</xsl:stylesheet>
