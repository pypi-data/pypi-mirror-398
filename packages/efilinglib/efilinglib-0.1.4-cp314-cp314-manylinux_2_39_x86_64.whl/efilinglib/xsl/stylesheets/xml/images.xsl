<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:jp="http://www.jpo.go.jp"
    xmlns:my="my"
    exclude-result-prefixes="my">

    <xsl:output method="xml" encoding="utf-8" indent="yes" />
    <xsl:import href="parts/common.xsl"/>

    <!-- 文書のID(ファイル名より)-->
    <xsl:param name="id" select="/root/metadata/id" />

    <xsl:template match="/root">
        <xsl:apply-templates select="images" />
    </xsl:template>

    <!-- 画像 -->
    <xsl:template match="images">
        <xsl:element name="images">
            <xsl:apply-templates select="image" />
        </xsl:element>
    </xsl:template>

    <xsl:template match="image">
        <!-- 変換前の画像ファイル名-->
        <xsl:variable name="orig" select="@orig" />

        <!-- 変換前の画像ファイルを参照しているノードを探す-->
        <xsl:variable name="img-node" select="//img[@file=$orig]" />

        <!-- そのノードの親ノードから属性num を図番とする-->
        <xsl:variable name="img-number" select="$img-node/parent::node()/@num" />

        <!-- 代表図のファイル名 -->
        <xsl:variable name="repr"
            select="//procedure-param[@name='representation-image']/@file-name" />

        <!-- 図面の簡単な説明から図番号に対応するものを得る -->
        <xsl:variable name="desc" select="//description-of-drawings//figref[@num=$img-number]" />

        <xsl:element name="image">
            <!-- 画像IDは、文書ID-通し番号 とする -->
            <xsl:variable name="iid">
                <xsl:value-of select="$id || '-'" />
                <xsl:call-template name="zero-pad">
                    <xsl:with-param name="number" select="position()"/>
                    <xsl:with-param name="length" select="3"/>
                </xsl:call-template>
            </xsl:variable>

            <xsl:element name="id">
                <xsl:value-of select="$iid" />
            </xsl:element>
            <xsl:element name="documentId">
                <xsl:value-of select="$id" />
            </xsl:element>
            <xsl:element name="number">
                <xsl:for-each select="//img[@file=$orig]">
                    <xsl:value-of select="parent::node()/@num" />
                </xsl:for-each>
            </xsl:element>
            <xsl:element name="filename">
                <xsl:value-of select="@new" />
            </xsl:element>
            <xsl:element name="kind">
                <xsl:value-of select="@kind" />
            </xsl:element>
            <xsl:element name="size_tag">
                <xsl:value-of select="@size_tag" />
            </xsl:element>
            <xsl:element name="width">
                <xsl:value-of select="@width" />
            </xsl:element>
            <xsl:element name="height">
                <xsl:value-of select="@height" />
            </xsl:element>
            <xsl:element name="representative">
                <xsl:choose>
                    <xsl:when test="@orig=$repr">
                        <xsl:value-of select="true()" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="false()" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:element>
            <xsl:element name="description">
                <xsl:value-of select="$desc" />
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- override build-in template for text and attribute nodes. -->
    <xsl:template match="text()|@*">
        <!-- <xsl:value-of select="normalize-space(.)"/> -->
    </xsl:template>
</xsl:stylesheet>