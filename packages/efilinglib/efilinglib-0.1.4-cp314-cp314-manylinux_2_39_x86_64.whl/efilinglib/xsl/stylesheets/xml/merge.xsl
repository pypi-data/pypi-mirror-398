<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:jp="http://www.jpo.go.jp"
                xmlns:ns0="http://www.jpo.go.jp"
                exclude-result-prefixes="ns0">
    
    <xsl:output method="xml" encoding="utf-8" indent="no" />
    
    <!-- this xsl processes a src xml file with following format.
         <files>
         <file href="file1.xml" />
         <file href="file2.xml" />
         </files>
         
         then all contents of the files are merged to one xml.
         namespace 'jp' is kept in output xml.
         file1.xml: <jp:a>hoge</jp:a>
         file2.xml: <b>fuga</b>
         output.xml: <root><jp:a>hoge</jp:a><b>fuga</b></root>
    -->
    <xsl:template match="/">
        <xsl:element name="root">
            <xsl:apply-templates select="files/file"/>
        </xsl:element>
    </xsl:template>
    
    <!--
         Read the root elements from document(@href). Using Saxon,
         the namespace prefix of the src xml will be changed another prefix on reading.
         e.g. prefix 'jp' is changed to 'ns0'
    -->
    <xsl:template match="file">
        <xsl:apply-templates select="document(@href)/*"/>
    </xsl:template>
    
    <!-- restore the prefix 'ns0' to 'jp'. -->
    <xsl:template match="ns0:*" mode="#default">
        <xsl:element name="jp:{local-name()}">
            <xsl:apply-templates select="@*|node()"/>
        </xsl:element>
    </xsl:template>
    
    <!-- also restore the prefix about attributes. -->
    <xsl:template match="@ns0:*">
        <xsl:attribute name="jp:{local-name()}" select="."/>
    </xsl:template>
    
    <!-- nodes and attributes with no prefix 'ns0' will be copied as is. -->
    <xsl:template match="@*|node()" mode="#default">
        <xsl:copy-of select="." copy-namespaces="false"/>
    </xsl:template>
</xsl:stylesheet>
