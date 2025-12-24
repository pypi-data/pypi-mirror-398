<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="3.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xs="http://www.w3.org/2001/XMLSchema"
                xmlns:jp="http://www.jpo.go.jp" >
  
  <!-- this xslt was created with reference to cpy-ntc-pat-e-rn.xsl
       of Internet Application Software version i5.30 provided by JPO -->
  
  
  <!--begin 令和 at the date. -->
  <xsl:variable name="date-r" select="20190501" />
  <!-- 2018 -> 令和0年 -->
  <xsl:variable name="year-r0" select="2018" />
  
  <!--begin 平成 at the date-->
  <xsl:variable name="date-h" select="19890108" />
  <xsl:variable name="year-h0" select="1988" />
  
  <!--begin 昭和 at the date-->
  <xsl:variable name="date-s" select="19261225" />
  <xsl:variable name="year-s0" select="1925" />
  
  <!--begin 大正 at the date-->
  <xsl:variable name="date-t" select="19120730" />
  <xsl:variable name="year-t0" select="1911" />
  
  <!--begin 明治 at the date-->
  <xsl:variable name="date-m" select="18680908" />
  <xsl:variable name="year-m0" select="1867" />
  
  <!-- ====================================================================
       元号編集
       ====================================================================-->
  <xsl:template name="gengo">
    <xsl:param name="date" as="xs:string"/>
    <xsl:variable name="int-date" as="xs:integer">
      <xsl:choose>
        <xsl:when test="string-length($date) != 8">
          <xsl:value-of select="-1"/> 
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="xs:integer($date)"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    
    <xsl:choose>
      <xsl:when test="$int-date = -1"/>
      <xsl:when test="$int-date &gt;= $date-r">
        <xsl:value-of select="'令和'" />
      </xsl:when>
      <xsl:when test="$int-date &gt;= $date-h">
        <xsl:value-of select="'平成'" />
      </xsl:when>
      <xsl:when test="$int-date &gt;= $date-s">
        <xsl:value-of select="'昭和'" />
      </xsl:when>
      <xsl:when test="$int-date &gt;= $date-t">
        <xsl:value-of select="'大正'" />
      </xsl:when>
      <xsl:when test="$int-date &gt;= $date-m">
        <xsl:value-of select="'明治'" />
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="'不明'" />
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  
  <!-- ====================================================================
       和暦年編集
       ====================================================================-->
  <xsl:template name="warekinen">
    <xsl:param name="date" as="xs:string"/>
    <xsl:variable name="int-date" as="xs:integer">
      <xsl:choose>
        <xsl:when test="string-length($date) != 8">
          <xsl:value-of select="-1"/> 
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="xs:integer($date)"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    
    <xsl:choose>
      <xsl:when test="$int-date = -1"/>
      <xsl:when test="$int-date &gt;= $date-r">
        <xsl:value-of select="floor($int-date div 10000) - $year-r0" />
      </xsl:when>
      <xsl:when test="$int-date &gt;= $date-h">
        <xsl:value-of select="floor($int-date div 10000) - $year-h0" />
      </xsl:when>
      <xsl:when test="$int-date &gt;= $date-s">
        <xsl:value-of select="floor($int-date div 10000) - $year-s0" />
      </xsl:when>
      <xsl:when test="$int-date &gt;= $date-t">
        <xsl:value-of select="floor($int-date div 10000) - $year-t0" />
      </xsl:when>
      <xsl:when test="$int-date &gt;= $date-m">
        <xsl:value-of select="floor($int-date div 10000) - $year-m0" />
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="'不明'" />
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  
</xsl:stylesheet>
