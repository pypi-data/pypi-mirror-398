<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:jp="http://www.jpo.go.jp" exclude-result-prefixes="jp">
    
    <xsl:output method="xml" encoding="utf-8" indent="yes"/>
    
    <!-- 手続ファイル(*FM.XML)から必要そうなタグだけを抽出してXML化する XSL -->
    <xsl:template match="/">
        <procedure-params>
            <xsl:apply-templates/>
        </procedure-params>
    </xsl:template>
   
    <!-- 整理番号、発明の名称、登録番号、出願番号,
         国際出願番号, 審判番号, 受領番号 -->
    <xsl:template match="jp:file-reference-id | jp:reference-id | jp:invention-title | 
        jp:registration-number | jp:application-number | 
        jp:international-application-number | jp:appeal-reference-number | jp:receipt-number">
        <xsl:element name="procedure-param">
            <xsl:attribute name="name">
                <xsl:value-of select="local-name(.)"/>
            </xsl:attribute>
            <xsl:value-of select="."/>
        </xsl:element>
    </xsl:template>
    
    <!-- 文書名と文書コード,法律 -->
    <xsl:template match="jp:document-name">
        <xsl:element name="procedure-param">
            <xsl:attribute name="name">
                <xsl:value-of select="local-name(.)"/>
            </xsl:attribute>
            <xsl:value-of select="."/>
        </xsl:element>
        
        <xsl:element name="procedure-param">
            <xsl:attribute name="name">document-code</xsl:attribute>
            <xsl:value-of select="@jp:document-code"/>
        </xsl:element>
        
        <!-- 1:特許, 2:実, 3:意, 4:商-->
        <xsl:element name="procedure-param">
            <xsl:attribute name="name">law</xsl:attribute>
            <xsl:value-of select="substring(@jp:document-code, 2, 1)"/>
        </xsl:element>
    </xsl:template>
    
    <!-- 提出日と発送日 -->
    <xsl:template match="jp:submission-date | jp:dispatch-date |
        jp:international-application-date | jp:appeal-reference-date">
        <xsl:element name="procedure-param">
            <xsl:attribute name="name">
                <xsl:value-of select="local-name(.)"/>
            </xsl:attribute>
            <xsl:element name="date">
                <xsl:value-of select="./jp:date"/>
            </xsl:element>
            <xsl:element name="time">
                <xsl:value-of select="./jp:time"/>
            </xsl:element>
        </xsl:element>
    </xsl:template>
    
    <!-- 出願人一覧 -->
    <xsl:template match="jp:applicant-article">
        <xsl:element name="procedure-param">
            <xsl:attribute name="name">applicants</xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>
    
    <!-- 出願人 -->
    <xsl:template match="jp:applicant">
        <xsl:element name="applicant">
            <xsl:attribute name="division">
                <xsl:value-of select="@jp:division"/>
            </xsl:attribute>
            <xsl:attribute name="id-number">
                <xsl:value-of select="./jp:identification-number"/>
            </xsl:attribute>
            <xsl:attribute name="name">
                <xsl:value-of select="./jp:name"/>
            </xsl:attribute>
        </xsl:element>
    </xsl:template>
    
    <!-- 代表図 -->
    <xsl:template match="jp:representation-image">
        <xsl:element name="procedure-param">
            <xsl:attribute name="name">
                <xsl:value-of select="local-name(.)"/>
            </xsl:attribute>
            <xsl:attribute name="title">
                <xsl:value-of select="./jp:title"/>
            </xsl:attribute>
            <xsl:attribute name="file-name">
                <xsl:value-of select="./jp:file-name"/>
            </xsl:attribute>
        </xsl:element>
    </xsl:template>
    
    <!-- override build-in template for text and attribute nodes. -->
    <xsl:template match="text()|@*">
        <!-- <xsl:value-of select="."/> -->
    </xsl:template>
</xsl:stylesheet>
