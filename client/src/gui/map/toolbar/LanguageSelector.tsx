import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  IconButton,
  Menu,
  MenuItem,
  Tooltip,
  Typography
} from '@mui/material';
import LanguageIcon from '@mui/icons-material/Language';

export default function LanguageSelector() {
  const { i18n, t } = useTranslation();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
    localStorage.setItem('language', lng);
    handleClose();
  };

  return (
    <>
      <Tooltip title={t('toolbar.language.selectLanguage')}>
        <IconButton
          color="inherit"
          onClick={handleClick}
          sx={{
            color: '#171717'
          }}
        >
          <LanguageIcon />
        </IconButton>
      </Tooltip>
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        <MenuItem onClick={() => changeLanguage('en')}>
          <Typography>
            {t('toolbar.language.english')}
          </Typography>
        </MenuItem>
        <MenuItem onClick={() => changeLanguage('zh')}>
          <Typography>
            {t('toolbar.language.chinese')}
          </Typography>
        </MenuItem>
      </Menu>
    </>
  );
}
