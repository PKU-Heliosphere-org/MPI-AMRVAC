# 在项目目录创建backup_amrvac.sh
cat > backup_amrvac.sh << 'EOF'
#!/bin/bash
if [ -f amrvac.f ]; then
    timestamp=$(date +"%Y%m%d_%H%M%S")
    backup_file="amrvac_backup_${timestamp}.f"
    cp amrvac.f "$backup_file"
    echo "Backup created: $backup_file"
fi
EOF
chmod +x backup_amrvac.sh