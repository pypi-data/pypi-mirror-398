<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="3.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xs="http://www.w3.org/2001/XMLSchema"
                xmlns:jp="http://www.jpo.go.jp">
    
    <xsl:template name="ERROR">
        <xsl:element name="div">
            <xsl:text>***WARNING unsupported tag:</xsl:text>
            <xsl:value-of select="name(.)" />
        </xsl:element>
    </xsl:template>
    
    <!-- 指定文字数になるまで末尾に全角空白を追加する
         param name="str": 空白が追加される文字列
         param name="length": 指定文字数 デフォルト11文字、最大20
         e.g.) str='ほげほげ' length=5
         ->      'ほげほげ　' 
    -->
    <xsl:template name="space-suffix">
        <xsl:param name="str" />
        <xsl:param name="length" select="11" />
        <xsl:variable name="strlen" select="string-length($str)"/>
        <xsl:variable name="suffix-chars">
            <xsl:call-template name="repeat-chars">
                <xsl:with-param name="char"  select="'　'"/>
                <xsl:with-param name="count" select="20"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="suffixed" select="$str || $suffix-chars" />
        <xsl:choose>
            <xsl:when test="$strlen >= $length">
                <xsl:value-of select="$str || '　'" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="substring($suffixed, 1, $length)" />  <!-- substring returns string with 1-based index -->
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <xsl:template name="space-suffix-11">
        <xsl:param name="tag" as="xs:string"/>
        <xsl:param name="padding" as="xs:string" select="'　　'"/>
        <xsl:call-template name="space-suffix">
            <xsl:with-param name="str" as="xs:string">
                <xsl:choose>
                    <xsl:when test="ancestor::jp:contents-of-amendment">
                        <xsl:value-of select="$padding || $tag" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$tag" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:with-param>
            <xsl:with-param name="length" select="11"/>
        </xsl:call-template>
    </xsl:template> 
    
    <!-- 
         $input-string の先頭に $length になるまで $pdding-char を付加する
         e.g. input-string='2', $length=2, $padding-char=' '
         -> ' 2'
    -->
    <xsl:template name="padding-beginning-of-string">
        <xsl:param name="input-string" as="xs:string"/>
        <xsl:param name="padding-char" select="' '" />
        <xsl:param name="length" select="2" />
        <xsl:variable name="padding-chars">
            <xsl:call-template name="repeat-chars">
                <xsl:with-param name="char" select="$padding-char"/>
                <xsl:with-param name="count" select="$length"/>
            </xsl:call-template>
            <xsl:value-of select="$input-string"/>
        </xsl:variable>
        <xsl:value-of select="substring($padding-chars, string-length($padding-chars) - $length + 1)"/>
    </xsl:template>
    
    <!-- 
         repeat $char to $count
         e.g.  $char='x' $count=3
         -> 'xxx'
    -->
    <xsl:template name="repeat-chars">
        <xsl:param name="char" select="' '" />
        <xsl:param name="count" select="11" />
        <xsl:for-each select="1 to $count">
            <xsl:value-of select="$char" />
        </xsl:for-each>
    </xsl:template>
    
    <!-- 
         split $input-string at every $n-chars and join with $sep
    -->
    <xsl:template name="split-at-n-chars">
        <xsl:param name="input-string" as="xs:string"/>
        <xsl:param name="n-chars" as="xs:integer" />
        <xsl:param name="sep" as="xs:string" select="' '"/>
        <xsl:variable name="length" select="string-length($input-string)"/>
        
        <xsl:for-each select="for $i in 1 to $length div $n-chars return $i">
            <xsl:value-of select="substring($input-string, (position() - 1) * $n-chars + 1, $n-chars)"/>
            <xsl:if test="position() != last()">
                <xsl:value-of select="$sep"/>
            </xsl:if>
        </xsl:for-each>
    </xsl:template> 
</xsl:stylesheet>
