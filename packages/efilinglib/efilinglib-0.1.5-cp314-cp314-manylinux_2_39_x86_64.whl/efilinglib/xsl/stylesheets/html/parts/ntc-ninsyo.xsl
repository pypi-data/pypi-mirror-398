<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:jp="http://www.jpo.go.jp"
                exclude-result-prefixes="jp">
    
  <!-- this xslt was created with reference to ntc-ninsyo.xsl
       of Internet Application Software version i5.30 provided by JPO -->
 
    <xsl:variable name="sp" select="'&#160;'" /> 
    <xsl:variable name="hankaku-apos" select='"&apos;"'/>
    <xsl:variable name="zenkaku-apos" select="'’'"/>
    <xsl:variable name="hankaku"
        select="'1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ().,-/!#$%*+:;=?@[\]^_`{|}~&amp;&quot;&lt;&gt;&#160;'" />
    <xsl:variable name="zenkaku"
        select="'１２３４５６７８９０ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ（）．，－／！＃＄％＊＋：；＝？＠［￥］＾＿‘｛｜｝～＆”＜＞　'" />
    <xsl:variable name="hankaku2" select="'1234567890-ABCDEFGHIJKLMNOPQRSTUVWXYZ'" />
    <xsl:variable name="zenkaku2" select="'１２３４５６７８９　－ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ'" />
    <xsl:variable name="kind-of-law">
        <xsl:choose>
            <xsl:when test="/root/procedure-params/procedure-param[@name='law'] = '1'">
                <xsl:value-of select="'patent'"/> 
            </xsl:when>
            <xsl:when test="/root/procedure-params/procedure-param[@name='law'] = '2'">
                <xsl:value-of select="'utility'"/> 
            </xsl:when>
            <xsl:when test="/root/procedure-params/procedure-param[@name='law'] = '3'">
                <!-- design may be '3' -->
                <xsl:value-of select="'utility'"/> 
            </xsl:when>
            <xsl:when test="/root/procedure-params/procedure-param[@name='law'] = '4'">
                <!-- trademark may be '3' -->
                <xsl:value-of select="'trademark'"/> 
            </xsl:when>
            <xsl:when test="substring(name(*),1,6) = 'jp:cpy'">
                <xsl:value-of select="*/*/*/@jp:kind-of-law[1]" />
            </xsl:when>
            <xsl:when test="substring(name(*),1,6) = 'jp:prt'">
                <xsl:value-of select="*/*/*/@jp:kind-of-law[1]" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="*/*/@jp:kind-of-law[1]" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    
    <!-- ====================================================================
         jp:certification-column-article
         ====================================================================-->
    <!-- 認証欄  -->
    <xsl:template match="jp:certification-column-article">
        <xsl:element name="div">
            <U>
                <xsl:value-of select="'　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　'" />
            </U>
        </xsl:element>
        <xsl:apply-templates select="jp:certification-column-group" />
        <xsl:apply-templates select="img" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:inquiry-article
         ====================================================================-->
    <!-- 問い合わせ文  -->
    <xsl:template match="jp:inquiry-article">
        <xsl:element name="div">
            <U>
                <xsl:value-of select="'　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　'" />
            </U>
        </xsl:element>
        <xsl:apply-templates select="p" />
        <xsl:apply-templates select="jp:inquiry-staff-group" />
        <xsl:apply-templates select="jp:phone" />
        <xsl:apply-templates select="jp:fax" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:certification-column-article/img
         ====================================================================-->
    <!-- 認証イメージ  -->
    <xsl:template match="jp:certification-column-article/img">
        <xsl:element name="IMG">
            <xsl:attribute name="SRC">
                <xsl:value-of select="./@file" />
            </xsl:attribute>
            <xsl:attribute name="WIDTH">
                <xsl:value-of select="./@wi" />
            </xsl:attribute>
            <xsl:attribute name="HEIGHT">
                <xsl:value-of select="./@he" />
            </xsl:attribute>
            <xsl:attribute name="ALIGN">
                <xsl:value-of select="'right'" />
            </xsl:attribute>
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         jp:certification-column-group
         ====================================================================-->
    <!-- 認証文 -->
    <xsl:template match="jp:certification-column-group">
        <xsl:apply-templates select="p[1]" />
        
        <xsl:element name="div">
            <xsl:apply-templates select="jp:certification-group" />
        </xsl:element>
        
        <xsl:choose>
            <xsl:when test="p[2]">
                <xsl:apply-templates select="p[2]" />
                <xsl:if test="jp:phone">
                    <xsl:apply-templates select="jp:phone" />
                    <xsl:apply-templates select="jp:fax" />
                </xsl:if>
            </xsl:when>
            
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="jp:inclusion-payment-group">
                        <xsl:element name="div">
                            <xsl:apply-templates select="jp:inclusion-payment-group" />
                        </xsl:element>
                    </xsl:when>
                    <xsl:otherwise>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
        
    </xsl:template>
    
    <!-- ====================================================================
         jp:certification-column-group/p | jp:inquiry-article/p
         ====================================================================-->
    <!-- 段落 -->
    <xsl:template match="jp:certification-column-group/p | jp:inquiry-article/p">
        <xsl:element name="div">
            <xsl:apply-templates />
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         jp:inquiry-staff-group
         ====================================================================-->
    <!-- 担当者情報 -->
    <xsl:template match="jp:inquiry-staff-group">
        <xsl:apply-templates select="jp:division" />
        <xsl:apply-templates select="jp:name" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:certification-group
         ====================================================================-->
    <!--  認証情報 -->
    <xsl:template match="jp:certification-group">
        <xsl:apply-templates select="jp:date" />
        <xsl:apply-templates select="jp:official-title" />
        <xsl:apply-templates select="jp:name" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:inclusion-payment-group
         ====================================================================-->
    <!--  包括納付情報 -->
    <xsl:template match="jp:inclusion-payment-group">
        <xsl:value-of select="'包括納付対象案件　'" />
        <xsl:apply-templates select="jp:account" />
        <xsl:apply-templates select="jp:payment-years" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:certification-column-group/jp:phone |
         jp:inquiry-article//jp:phone
         ====================================================================-->
    <!--  電話番号 -->
    <xsl:template
        match="jp:certification-column-group/jp:phone
            | jp:inquiry-article//jp:phone">
        <xsl:variable name="tel1" select="string-length(substring-before(normalize-space(.),'-'))" />
        <xsl:variable name="tel2"
            select="string-length(substring-before(substring(normalize-space(.),$tel1 + 2),'-'))" />
        <xsl:variable name="tel3"
            select="string-length(substring-before(substring(normalize-space(.),$tel1 + $tel2 + 3),'('))" />
        <xsl:variable name="tel4"
            select="string-length(substring-before(substring(normalize-space(.),$tel1 + $tel2 + $tel3 + 4),')'))" />
        
        <xsl:element name="div">
            <xsl:choose>
                <xsl:when test="ancestor::jp:inquiry-article">
                    <xsl:value-of select="'　電話　'" />
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="'電話'" />
                </xsl:otherwise>
            </xsl:choose>
            
            <xsl:choose>
                <xsl:when test="./@jp:error-code">
                    <xsl:value-of select="." />
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of
                        select="concat(substring(normalize-space(.),1,$tel1),'(',
                                substring(normalize-space(.),($tel1 + 2),$tel2),')',
                                substring(normalize-space(.),($tel1 + $tel2 + 3),$tel3),'　内線',
                                substring(normalize-space(.),($tel1 + $tel2 + $tel3 + 4),$tel4))" />
                </xsl:otherwise>
            </xsl:choose>
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         jp:certification-column-group/jp:fax |
         jp:inquiry-article//jp:fax
         ====================================================================-->
    <!--  ファクシミリ番号 -->
    <xsl:template match="jp:certification-column-group/jp:fax | jp:inquiry-article//jp:fax">
        <xsl:if test="not(ancestor::jp:notice-transmit)">
            <xsl:variable name="fax1"
                select="string-length(substring-before(normalize-space(.),'-'))" />
            <xsl:variable name="fax2"
                select="string-length(substring-before(substring(normalize-space(.),$fax1 + 2),'-'))" />
            <xsl:variable name="fax3"
                select="string-length(substring(normalize-space(.),$fax1 + $fax2 + 3))" />
            <xsl:element name="div">
                <xsl:choose>
                    <xsl:when test="ancestor::jp:inquiry-article">
                        <xsl:value-of select="'　　　ファクシミリ　'" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="'　　　ファクシミリ'" />
                    </xsl:otherwise>
                </xsl:choose>
                
                <xsl:choose>
                    <xsl:when test="./@jp:error-code">
                        <xsl:value-of select="." />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of
                            select="concat(substring(normalize-space(.),1,$fax1),'(',
                                    substring(normalize-space(.),($fax1 + 2),$fax2),')',
                                    substring(normalize-space(.),($fax1 + $fax2 + 3),$fax3))" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:element>
        </xsl:if>
    </xsl:template>
    
    <!-- ====================================================================
         jp:division
         ====================================================================-->
    <!-- 所属  -->
    <xsl:template match="jp:division">
        <xsl:variable name="division" select="translate(.,' ','')" />
        <xsl:value-of select="'　' || $division" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:account
         ====================================================================-->
    <!-- 予納台帳番号・納付書番号  -->
    <xsl:template match="jp:account">
        <xsl:choose>
            <xsl:when test="./@account-type = 'deposit'">
                <xsl:value-of select="'予納台帳番号　'" />
            </xsl:when>
            
            <xsl:when test="./@account-type = 'transfer'">
                <xsl:value-of select="'振替番号　　　'" />
            </xsl:when>
            
            <xsl:otherwise>
                <xsl:value-of select="'納付書番号　　'" />
            </xsl:otherwise>
        </xsl:choose>
        
        <xsl:choose>
            <xsl:when test="./@jp:error-code">
                <xsl:value-of select="./@number" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="./@number" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <!-- ====================================================================
         jp:certification-group/jp:date
         ====================================================================-->
    <!-- 認証・日付  -->
    <xsl:template match="jp:certification-group/jp:date">
        
        <xsl:value-of select="'認証日　'" />
        
        <xsl:choose>
            <xsl:when test="./@jp:error-code">
                <xsl:value-of select="." />
            </xsl:when>
            
            <xsl:when test="number(.) = 0 or string-length(normalize-space(.)) = 0">
                <xsl:value-of select="'　　　　　　　　'" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="日付変換" />
            </xsl:otherwise>
        </xsl:choose>
        
    </xsl:template>
    
    <!-- ====================================================================
         jp:certification-group/jp:name
         jp:inquiry-article/jp:name 担当者・名前
         jp:certification-group/jp:official-title 認証・役職名
         ====================================================================-->
    <xsl:template match="jp:certification-group/jp:name | jp:inquiry-staff-group/jp:name |
        jp:certification-group/jp:official-title">
        <xsl:value-of select="'　' || normalize-space(.)" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:payment-years
         ====================================================================-->
    <!-- 納付年分     -->
    <xsl:template match="jp:payment-years">
        <xsl:element name="div">
            <xsl:value-of select="'　　　　　　　　　納付年分　　　'" />
            <xsl:apply-templates select="jp:year-from" />
            <xsl:apply-templates select="jp:year-to" />
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         jp:year-from
         ====================================================================-->
    <!-- 納付年分（自） -->
    <xsl:template match="jp:year-from">
        <xsl:choose>
            <xsl:when test="./@jp:error-code">
                <xsl:value-of select="." />
                <xsl:value-of select="'年～'" />
            </xsl:when>
            <xsl:when test="string-length(normalize-space(.)) = 0" />
            <xsl:otherwise>
                <xsl:value-of select="normalize-space(.) || '年～'" />
            </xsl:otherwise>
        </xsl:choose>
        
    </xsl:template>
    
    <!-- ====================================================================
         jp:year-to
         ====================================================================-->
    <!-- 納付年分（至） -->
    <xsl:template match="jp:year-to">
        <xsl:choose>
            <xsl:when test="./@jp:error-code">
                <xsl:value-of select="." />
                <xsl:value-of select="'年分'" />
            </xsl:when>
            <xsl:when test="string-length(normalize-space(.)) = 0" />
            <xsl:otherwise>
                <xsl:value-of select="normalize-space(.) || '年分'" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <!-- ====================================================================
         平成編集
         ====================================================================-->
    <xsl:template name="平成編集">
        <xsl:variable name="hyy" select="substring(normalize-space(.),1,4) - 1988" />
        <xsl:value-of select="'平成' || $hyy || '年'" />
    </xsl:template>
    
    <!-- ====================================================================
         昭和編集
         ====================================================================-->
    <xsl:template name="昭和編集">
        <xsl:variable name="syy" select="63 - (1988 - substring(normalize-space(.),1,4))" />
        <xsl:value-of select="'昭和' || $syy || '年'" />
    </xsl:template>
    
    <!-- ====================================================================
         大正編集
         ====================================================================-->
    <xsl:template name="大正編集">
        <xsl:variable name="tyy" select="15 - (1926 - substring(normalize-space(.),1,4))" />
        <xsl:value-of select="'大正' || $tyy || '年'" />
    </xsl:template>
    
    <!-- ====================================================================
         明治編集
         ====================================================================-->
    <xsl:template name="明治編集">
        <xsl:variable name="myy" select="45 - (1912 - substring(normalize-space(.),1,4))" />
        <xsl:value-of select="'明治' || $myy || '年'" />
    </xsl:template>
    
    <!-- ====================================================================
         未サポートタグ（jp:guidance）
         ====================================================================-->
    <xsl:template match="jp:guidance">
        <xsl:element name="div">
            <xsl:call-template name="タグ編集">
                <xsl:with-param name="i" select="2" />
            </xsl:call-template>
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         タグ編集
         ====================================================================-->
    <xsl:template name="タグ編集">
        <xsl:param name="i" select="2" />
        <xsl:element name="div">
            <xsl:value-of select="'&lt;' || name()" />
            <xsl:apply-templates select="./@*" />
            <xsl:value-of select="'&gt;' || . || '&lt;/' || name() || '&gt;'" />
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         属性値出力
         ====================================================================-->
    <xsl:template match="@file | @he | @wi | @img-format |@img-content">
        <xsl:value-of select="' ' || name() || '=&quot;' || . || '&quot;'" />
    </xsl:template>
</xsl:stylesheet>