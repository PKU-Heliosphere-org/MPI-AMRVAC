
# 在测试目录创建custom.make
cat > custom.make << 'EOF'
.PHONY: myclean 

myclean:
    @./backup_amrvac.sh
    $(MAKE) -f test.make clean

# 覆盖默认clean规则
clean: myclean
EOF

